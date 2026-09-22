/**
 * @file diagnostic.cpp
 * @brief Allocation-free diagnostic construction, ordering, and owned storage.
 * @ownership All accepted text is copied into fixed-capacity immutable values.
 * @lifetime No caller view is retained after creation.
 * @thread_safety Construction uses call-local state; const values support concurrent reads.
 * @failure Validated construction is noexcept; dynamic serialization may report bad_alloc.
 */

#include "xverse/xcom/diagnostic.hpp"

#include <algorithm>
namespace xverse::xcom {
namespace {

/**
 * @brief Validate one required bounded diagnostic text field.
 * @param value Candidate text.
 * @param maximum Maximum accepted byte count.
 * @return true only for non-empty bounded text without prohibited ASCII control bytes.
 * @failure This locale-independent operation cannot fail.
 */
[[nodiscard]] bool valid_text(const std::string_view value, const std::size_t maximum) noexcept {
  return !value.empty() && value.size() <= maximum &&
         std::ranges::none_of(value, [](const char character) {
           const auto byte = static_cast<unsigned char>(character);
           return (byte <= 0x1FU && character != '\t') || byte == 0x7FU;
         });
}

/** @brief Return whether code is a declared value. */
[[nodiscard]] bool known_code(const DiagnosticCode code) noexcept {
  switch (code) {
    case DiagnosticCode::required_field:
    case DiagnosticCode::bound_exceeded:
    case DiagnosticCode::invalid_version:
    case DiagnosticCode::incompatible_direction:
    case DiagnosticCode::contract_mismatch:
      return true;
  }
  return false;
}

/** @brief Return whether severity is a declared value. */
[[nodiscard]] bool known_severity(const DiagnosticSeverity severity) noexcept {
  switch (severity) {
    case DiagnosticSeverity::information:
    case DiagnosticSeverity::warning:
    case DiagnosticSeverity::error:
      return true;
  }
  return false;
}

/** @brief Return whether phase is a declared value. */
[[nodiscard]] bool known_phase(const ValidationPhase phase) noexcept {
  switch (phase) {
    case ValidationPhase::contract:
    case ValidationPhase::item:
      return true;
  }
  return false;
}

/**
 * @brief Append escaped text to a fixed ordering-key buffer.
 * @param output Destination storage.
 * @param used Initialized destination length on entry and exit.
 * @param value Text to escape and append.
 */
void append_escaped(std::array<char, Diagnostic::kMaximumOrderingKeyBytes>& output,
                    std::size_t& used, const std::string_view value) noexcept {
  for (const char character : value) {
    if (character == '\\' || character == '|') {
      output[used++] = '\\';
    }
    output[used++] = character;
  }
}

/**
 * @brief Build the canonical escaped ordering key in caller-owned storage.
 * @param input Valid diagnostic fields.
 * @return Fixed-capacity key storage.
 */
[[nodiscard]] detail::FixedText<Diagnostic::kMaximumOrderingKeyBytes> make_ordering_key(
    const DiagnosticInput& input) noexcept {
  std::array<char, Diagnostic::kMaximumOrderingKeyBytes> bytes{};
  std::size_t used = 0U;
  const auto append = [&bytes, &used](const std::string_view value) noexcept {
    append_escaped(bytes, used, value);
  };
  append(to_string(input.phase));
  bytes[used++] = '|';
  append(to_string(input.severity));
  bytes[used++] = '|';
  append(to_string(input.code));
  bytes[used++] = '|';
  append(input.affected_identity);
  bytes[used++] = '|';
  append(input.reason);
  bytes[used++] = '|';
  append(input.correction);
  detail::FixedText<Diagnostic::kMaximumOrderingKeyBytes> key;
  static_cast<void>(key.assign({bytes.data(), used}));
  return key;
}

}  // namespace

std::string_view to_string(const DiagnosticCode code) noexcept {
  switch (code) {
    case DiagnosticCode::required_field:
      return "XCOM-TYPE-E001";
    case DiagnosticCode::bound_exceeded:
      return "XCOM-TYPE-E002";
    case DiagnosticCode::invalid_version:
      return "XCOM-TYPE-E003";
    case DiagnosticCode::incompatible_direction:
      return "XCOM-TYPE-E004";
    case DiagnosticCode::contract_mismatch:
      return "XCOM-TYPE-E005";
  }
  return "XCOM-TYPE-E000";
}

std::string_view to_string(const DiagnosticSeverity severity) noexcept {
  switch (severity) {
    case DiagnosticSeverity::information:
      return "information";
    case DiagnosticSeverity::warning:
      return "warning";
    case DiagnosticSeverity::error:
      return "error";
  }
  return "unknown";
}

std::string_view to_string(const ValidationPhase phase) noexcept {
  switch (phase) {
    case ValidationPhase::contract:
      return "contract";
    case ValidationPhase::item:
      return "item";
  }
  return "unknown";
}

Diagnostic::Diagnostic(const DiagnosticInput& input) noexcept
    : code_(input.code), severity_(input.severity), phase_(input.phase) {
  static_cast<void>(affected_identity_.assign(input.affected_identity));
  static_cast<void>(reason_.assign(input.reason));
  static_cast<void>(correction_.assign(input.correction));
  ordering_key_ = make_ordering_key(input);
}

Diagnostic::Diagnostic() noexcept
    : Diagnostic({DiagnosticCode::required_field, DiagnosticSeverity::error,
                  ValidationPhase::contract, "internal", "unexposed diagnostic slot",
                  "construct through a validated factory"}) {}

void Diagnostic::replace_with(const Diagnostic& other) noexcept {
  code_ = other.code_;
  severity_ = other.severity_;
  phase_ = other.phase_;
  affected_identity_ = other.affected_identity_;
  reason_ = other.reason_;
  correction_ = other.correction_;
  ordering_key_ = other.ordering_key_;
}

std::optional<Diagnostic> Diagnostic::create(const DiagnosticInput& input) noexcept {
  if (!known_code(input.code) || !known_severity(input.severity) || !known_phase(input.phase) ||
      !valid_text(input.affected_identity, kMaximumIdentityBytes) ||
      !valid_text(input.reason, kMaximumTextBytes) ||
      !valid_text(input.correction, kMaximumTextBytes)) {
    return std::nullopt;
  }
  return Diagnostic(input);
}

std::string Diagnostic::serialize() const { return std::string(ordering_key()); }

std::optional<DiagnosticSet> DiagnosticSet::create(
    const std::span<const Diagnostic> diagnostics) noexcept {
  if (diagnostics.empty() || diagnostics.size() > kMaximumDiagnostics) {
    return std::nullopt;
  }
  DiagnosticSet set;
  set.size_ = diagnostics.size();
  for (std::size_t index = 0U; index < diagnostics.size(); ++index) {
    set.diagnostics_[index].replace_with(diagnostics[index]);
  }
  set.sort_initialized();
  return set;
}

std::optional<DiagnosticSet> DiagnosticSet::create_from_inputs(
    const std::span<const DiagnosticInput> inputs) noexcept {
  if (inputs.empty() || inputs.size() > kMaximumDiagnostics) {
    return std::nullopt;
  }
  DiagnosticSet set;
  for (const DiagnosticInput& input : inputs) {
    const auto diagnostic = Diagnostic::create(input);
    if (!diagnostic.has_value()) {
      return std::nullopt;
    }
    set.diagnostics_[set.size_].replace_with(*diagnostic);
    ++set.size_;
  }
  set.sort_initialized();
  return set;
}

void DiagnosticSet::sort_initialized() noexcept {
  for (std::size_t index = 1U; index < size_; ++index) {
    const Diagnostic current(diagnostics_[index]);
    std::size_t position = index;
    while (position > 0U &&
           current.ordering_key() < diagnostics_[position - 1U].ordering_key()) {
      diagnostics_[position].replace_with(diagnostics_[position - 1U]);
      --position;
    }
    diagnostics_[position].replace_with(current);
  }
}

std::string DiagnosticSet::serialize() const {
  std::string result;
  for (const Diagnostic& diagnostic : values()) {
    if (!result.empty()) {
      result.push_back('\n');
    }
    result.append(diagnostic.ordering_key());
  }
  return result;
}

bool operator==(const DiagnosticSet& left, const DiagnosticSet& right) noexcept {
  return std::ranges::equal(left.values(), right.values());
}

}  // namespace xverse::xcom

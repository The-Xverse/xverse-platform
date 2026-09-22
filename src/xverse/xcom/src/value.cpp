/**
 * @file value.cpp
 * @brief Allocation-free validation implementation for bounded core values.
 * @ownership Created values copy and own all accepted input.
 * @lifetime No input view is retained after a factory returns.
 * @thread_safety Functions use only call-local state and support concurrent calls.
 * @failure Invalid input returns an empty optional; validated construction is noexcept.
 */

#include "xverse/xcom/value.hpp"

#include <algorithm>
namespace xverse::xcom {
namespace {

/**
 * @brief Test whether one identity byte is forbidden.
 * @param character Unsigned byte value.
 * @return true for ASCII control bytes, independent of the caller's locale.
 * @failure This operation cannot fail.
 */
[[nodiscard]] bool has_forbidden_identity_byte(const unsigned char character) noexcept {
  return character <= 0x1FU || character == 0x7FU;
}

/**
 * @brief Test whether one byte is ASCII whitespace.
 * @param character Unsigned byte value.
 * @return true for the six ASCII whitespace bytes, independent of the caller's locale.
 * @failure This operation cannot fail.
 */
[[nodiscard]] bool is_ascii_whitespace(const unsigned char character) noexcept {
  return character == 0x20U || (character >= 0x09U && character <= 0x0DU);
}

/**
 * @brief Validate one canonical decimal semantic-version component.
 * @param component Candidate component bytes.
 * @return true only for canonical decimal digits without leading zeroes.
 * @failure This operation cannot fail.
 */
[[nodiscard]] bool valid_numeric_component(const std::string_view component) noexcept {
  if (component.empty() || (component.size() > 1U && component.front() == '0')) {
    return false;
  }
  return std::ranges::all_of(component, [](const unsigned char character) {
    return character >= static_cast<unsigned char>('0') &&
           character <= static_cast<unsigned char>('9');
  });
}

}  // namespace

std::optional<Identity> Identity::create(const std::string_view text) noexcept {
  if (text.empty() || text.size() > kMaximumIdentityBytes ||
      is_ascii_whitespace(static_cast<unsigned char>(text.front())) ||
      is_ascii_whitespace(static_cast<unsigned char>(text.back())) ||
      std::ranges::any_of(text, [](const char character) {
        return has_forbidden_identity_byte(static_cast<unsigned char>(character));
      })) {
    return std::nullopt;
  }
  detail::FixedText<kMaximumIdentityBytes> storage;
  static_cast<void>(storage.assign(text));
  return Identity(storage);
}

std::optional<SemanticVersion> SemanticVersion::create(const std::string_view text) noexcept {
  if (text.empty() || text.size() > kMaximumVersionBytes) {
    return std::nullopt;
  }
  const std::size_t first_dot = text.find('.');
  if (first_dot == std::string_view::npos) {
    return std::nullopt;
  }
  const std::size_t second_dot = text.find('.', first_dot + 1U);
  if (second_dot == std::string_view::npos ||
      text.find('.', second_dot + 1U) != std::string_view::npos ||
      !valid_numeric_component(text.substr(0U, first_dot)) ||
      !valid_numeric_component(text.substr(first_dot + 1U, second_dot - first_dot - 1U)) ||
      !valid_numeric_component(text.substr(second_dot + 1U))) {
    return std::nullopt;
  }
  detail::FixedText<kMaximumVersionBytes> storage;
  static_cast<void>(storage.assign(text));
  return SemanticVersion(storage);
}

Payload::Payload(const std::span<const std::byte> bytes) noexcept : size_(bytes.size()) {
  std::ranges::copy(bytes, bytes_.begin());
}

std::optional<Payload> Payload::create(const std::span<const std::byte> bytes) noexcept {
  if (bytes.size() > kMaximumPayloadBytes) {
    return std::nullopt;
  }
  return Payload(bytes);
}

}  // namespace xverse::xcom

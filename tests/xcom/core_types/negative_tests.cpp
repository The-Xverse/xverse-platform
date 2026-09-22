/**
 * @file negative_tests.cpp
 * @brief Requirement-based boundary, rejection, and exact-diagnostic checks.
 * @ownership Each case owns its mutation buffers and returned diagnostic result.
 * @lifetime No view is retained beyond the owning result or active source fixture.
 * @thread_safety The executable is single-threaded; library validation is call-local.
 * @failure The executable reports each failed rejection invariant and returns nonzero.
 */

#include "xverse/xcom/core_types.hpp"

#include <array>
#include <clocale>
#include <cstddef>
#include <iostream>
#include <string>
#include <string_view>
#include <vector>

namespace {

using namespace xverse::xcom;

/**
 * @brief Report one failed negative expectation.
 * @param condition Expected boolean condition.
 * @param message Failure detail.
 * @return The original condition.
 */
[[nodiscard]] bool expect(const bool condition, const std::string_view message) {
  if (!condition) {
    std::cerr << "negative failure: " << message << '\n';
  }
  return condition;
}

/** @return A valid immutable message/event contract fixture. */
[[nodiscard]] CommunicationContract valid_contract() {
  const auto result = CommunicationContract::create(
      {"contract.alpha", "1.0.0", "interface.alpha", "schema.alpha", "1.0.0",
       InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume});
  return *result.value();
}

/** @return A complete call-scoped item input fixture. */
[[nodiscard]] CommunicationItemInput valid_item_input() {
  static constexpr std::array<std::byte, 1U> payload{std::byte{0x01}};
  return {"contract.alpha", "1.0.0", "interface.alpha", "endpoint.alpha", "schema.alpha",
          "1.0.0", InteractionKind::message_event, OriginKind::provider_generated, Timestamp(7),
          "clock.monotonic", "correlation.alpha", "causation.alpha", "route.alpha",
          "provider.alpha", payload};
}

/**
 * @brief Test whether a diagnostic sequence contains one exact code.
 * @param diagnostics Non-empty diagnostic set.
 * @param code Required code.
 * @return true when any diagnostic has the code.
 */
[[nodiscard]] bool has_code(const DiagnosticSet& diagnostics, const DiagnosticCode code) {
  for (const Diagnostic& diagnostic : diagnostics.values()) {
    if (diagnostic.code() == code) {
      return true;
    }
  }
  return false;
}

/** @return true when every incompatible interaction tuple produces E004. */
[[nodiscard]] bool test_invalid_direction_table() {
  struct Case final {
    InteractionKind kind;       /**< Candidate interaction semantics. */
    EndpointDirection source;   /**< Incompatible source direction. */
    EndpointDirection target;   /**< Incompatible target direction. */
  };
  constexpr std::array<Case, 6U> cases{{
      {InteractionKind::signal_state_update, EndpointDirection::consume,
       EndpointDirection::produce},
      {InteractionKind::message_event, EndpointDirection::request, EndpointDirection::respond},
      {InteractionKind::service_request, EndpointDirection::produce, EndpointDirection::consume},
      {InteractionKind::service_response, EndpointDirection::request, EndpointDirection::respond},
      {static_cast<InteractionKind>(255), EndpointDirection::produce, EndpointDirection::consume},
      {InteractionKind::message_event, static_cast<EndpointDirection>(255),
       EndpointDirection::consume},
  }};
  for (const Case& entry : cases) {
    const auto result = CommunicationContract::create(
        {"contract.alpha", "1.0.0", "interface.alpha", "schema.alpha", "1.0.0", entry.kind,
         entry.source, entry.target});
    if (!expect(!result.has_value() && result.value() == nullptr && result.diagnostics() != nullptr,
                "incompatible directions did not produce exclusive failure") ||
        !expect(result.diagnostics()->size() == 1U, "direction failure count differs") ||
        !expect(has_code(*result.diagnostics(), DiagnosticCode::incompatible_direction),
                "incompatible-direction code missing")) {
      return false;
    }
  }
  return true;
}

/** @return true when every contract text field enforces its exact boundary and syntax. */
[[nodiscard]] bool test_contract_field_boundaries() {
  using Member = std::string_view CommunicationContractInput::*;
  constexpr std::array<Member, 3U> identity_fields{
      &CommunicationContractInput::contract_id,
      &CommunicationContractInput::interface_id,
      &CommunicationContractInput::schema_id,
  };
  constexpr std::array<Member, 2U> version_fields{
      &CommunicationContractInput::contract_version,
      &CommunicationContractInput::schema_version,
  };
  const std::string maximum_identity(kMaximumIdentityBytes, 'i');
  const std::string oversized_identity(kMaximumIdentityBytes + 1U, 'i');
  const std::string maximum_version = "1234567890123456789012345678.0.0";
  const std::string oversized_version = "12345678901234567890123456789.0.0";

  for (const Member field : identity_fields) {
    CommunicationContractInput valid{"contract.alpha", "1.0.0", "interface.alpha",
                                     "schema.alpha", "1.0.0", InteractionKind::message_event,
                                     EndpointDirection::produce, EndpointDirection::consume};
    valid.*field = maximum_identity;
    if (!expect(CommunicationContract::create(valid).has_value(),
                "maximum contract identity boundary was rejected")) {
      return false;
    }
    for (const std::string_view invalid : {std::string_view{}, std::string_view{oversized_identity}}) {
      auto input = valid;
      input.*field = invalid;
      const auto result = CommunicationContract::create(input);
      if (!expect(!result.has_value() && result.diagnostics() != nullptr,
                  "invalid contract identity boundary was accepted")) {
        return false;
      }
    }
  }

  for (const Member field : version_fields) {
    CommunicationContractInput valid{"contract.alpha", "1.0.0", "interface.alpha",
                                     "schema.alpha", "1.0.0", InteractionKind::message_event,
                                     EndpointDirection::produce, EndpointDirection::consume};
    valid.*field = maximum_version;
    if (!expect(CommunicationContract::create(valid).has_value(),
                "maximum contract version boundary was rejected")) {
      return false;
    }
    constexpr std::array<std::string_view, 4U> malformed{"", "01.0.0", "1.0", "1.a.0"};
    for (const std::string_view invalid : malformed) {
      auto input = valid;
      input.*field = invalid;
      if (!expect(!CommunicationContract::create(input).has_value(),
                  "malformed contract version was accepted")) {
        return false;
      }
    }
    auto over_bound = valid;
    over_bound.*field = oversized_version;
    if (!expect(!CommunicationContract::create(over_bound).has_value(),
                "over-bound contract version was accepted")) {
      return false;
    }
  }

  auto lexical = CommunicationContractInput{
      "contract.alpha", "1.0.0", "interface.alpha", "schema.alpha", "1.0.0",
      InteractionKind::message_event, EndpointDirection::produce, EndpointDirection::consume};
  lexical.schema_id = "bad\nidentity";
  return expect(!CommunicationContract::create(lexical).has_value(),
                "control-containing contract identity was accepted");
}

/** @return true when every required item identity and version enforces all boundaries. */
[[nodiscard]] bool test_item_field_boundaries() {
  using Member = std::string_view CommunicationItemInput::*;
  constexpr std::array<Member, 9U> identity_fields{
      &CommunicationItemInput::contract_id, &CommunicationItemInput::interface_id,
      &CommunicationItemInput::endpoint_id, &CommunicationItemInput::schema_id,
      &CommunicationItemInput::clock_domain, &CommunicationItemInput::correlation_id,
      &CommunicationItemInput::causation_id, &CommunicationItemInput::route_id,
      &CommunicationItemInput::provider_id,
  };
  constexpr std::array<Member, 2U> version_fields{
      &CommunicationItemInput::contract_version,
      &CommunicationItemInput::schema_version,
  };
  const std::string oversized_identity(kMaximumIdentityBytes + 1U, 'x');
  const std::string oversized_version(kMaximumVersionBytes + 1U, '1');
  const CommunicationContract contract = valid_contract();

  for (const Member field : identity_fields) {
    for (const std::string_view invalid : {std::string_view{}, std::string_view{oversized_identity}}) {
      auto input = valid_item_input();
      input.*field = invalid;
      const auto result = CommunicationItem::create(input, contract);
      if (!expect(!result.has_value() && result.diagnostics() != nullptr,
                  "invalid item identity boundary was accepted")) {
        return false;
      }
    }
  }
  for (const Member field : version_fields) {
    for (const std::string_view invalid :
         {std::string_view{}, std::string_view{"1"}, std::string_view{oversized_version}}) {
      auto input = valid_item_input();
      input.*field = invalid;
      const auto result = CommunicationItem::create(input, contract);
      if (!expect(!result.has_value() && result.diagnostics() != nullptr,
                  "invalid item version boundary was accepted")) {
        return false;
      }
    }
  }

  auto mismatched = valid_item_input();
  mismatched.contract_id = "contract.other";
  if (!expect(has_code(*CommunicationItem::create(mismatched, contract).diagnostics(),
                       DiagnosticCode::contract_mismatch),
              "contract metadata mismatch was not rejected")) {
    return false;
  }
  auto kind = valid_item_input();
  kind.interaction_kind = InteractionKind::service_request;
  if (!expect(!CommunicationItem::create(kind, contract).has_value(),
              "interaction mismatch was accepted")) {
    return false;
  }
  auto origin = valid_item_input();
  origin.origin = static_cast<OriginKind>(255);
  if (!expect(!CommunicationItem::create(origin, contract).has_value(),
              "unknown origin was accepted")) {
    return false;
  }
  const std::vector<std::byte> oversized_payload(kMaximumPayloadBytes + 1U, std::byte{0});
  auto payload = valid_item_input();
  payload.payload = oversized_payload;
  return expect(!CommunicationItem::create(payload, contract).has_value(),
                "over-bound payload was accepted");
}

/** @return true when diagnostic enumerations and every text boundary are exact. */
[[nodiscard]] bool test_diagnostic_boundaries_and_codes() {
  const auto make = [](const DiagnosticCode code, const DiagnosticSeverity severity,
                       const ValidationPhase phase, const std::string_view identity,
                       const std::string_view reason, const std::string_view correction) {
    return Diagnostic::create({code, severity, phase, identity, reason, correction});
  };
  const std::string identity_limit(kMaximumIdentityBytes, 'i');
  const std::string identity_over(kMaximumIdentityBytes + 1U, 'i');
  const std::string text_limit(Diagnostic::kMaximumTextBytes, 't');
  const std::string text_over(Diagnostic::kMaximumTextBytes + 1U, 't');
  if (!expect(make(DiagnosticCode::required_field, DiagnosticSeverity::error,
                   ValidationPhase::item, identity_limit, text_limit, text_limit).has_value(),
              "maximum diagnostic text boundaries were rejected")) {
    return false;
  }
  const std::array invalid{
      make(static_cast<DiagnosticCode>(255), DiagnosticSeverity::error, ValidationPhase::item,
           "identity", "reason", "correction"),
      make(DiagnosticCode::required_field, static_cast<DiagnosticSeverity>(255),
           ValidationPhase::item, "identity", "reason", "correction"),
      make(DiagnosticCode::required_field, DiagnosticSeverity::error,
           static_cast<ValidationPhase>(255), "identity", "reason", "correction"),
      make(DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::item,
           "", "reason", "correction"),
      make(DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::item,
           identity_over, "reason", "correction"),
      make(DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::item,
           "identity", "", "correction"),
      make(DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::item,
           "identity", text_over, "correction"),
      make(DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::item,
           "identity", "reason", ""),
      make(DiagnosticCode::required_field, DiagnosticSeverity::error, ValidationPhase::item,
           "identity", "reason", text_over),
  };
  for (const auto& diagnostic : invalid) {
    if (!expect(!diagnostic.has_value(), "invalid diagnostic field was accepted")) {
      return false;
    }
  }
  return expect(to_string(DiagnosticCode::required_field) == "XCOM-TYPE-E001", "E001 differs") &&
         expect(to_string(DiagnosticCode::bound_exceeded) == "XCOM-TYPE-E002", "E002 differs") &&
         expect(to_string(DiagnosticCode::invalid_version) == "XCOM-TYPE-E003", "E003 differs") &&
         expect(to_string(DiagnosticCode::incompatible_direction) == "XCOM-TYPE-E004",
                "E004 differs") &&
         expect(to_string(DiagnosticCode::contract_mismatch) == "XCOM-TYPE-E005", "E005 differs");
}

/** @return true when a reordered invalid set yields one exact serialized sequence. */
[[nodiscard]] bool test_exact_multi_error_sequence() {
  auto first = valid_item_input();
  first.route_id = "";
  first.contract_id = "contract.other";
  first.schema_version = "invalid";

  auto second = valid_item_input();
  second.schema_version = "invalid";
  second.contract_id = "contract.other";
  second.route_id = "";

  const auto first_result = CommunicationItem::create(first, valid_contract());
  const auto second_result = CommunicationItem::create(second, valid_contract());
  const std::string expected =
      "item|error|XCOM-TYPE-E001|route_id|required identity is empty|provide a non-empty bounded identity\n"
      "item|error|XCOM-TYPE-E003|schema_version|version is not bounded canonical major.minor.patch|provide three decimal components without leading zeroes\n"
      "item|error|XCOM-TYPE-E005|contract_id|item metadata differs from its communication contract|use the exact immutable contract value\n"
      "item|error|XCOM-TYPE-E005|schema_version|item metadata differs from its communication contract|use the exact immutable contract value";
  return expect(first_result.diagnostics() != nullptr && second_result.diagnostics() != nullptr,
                "multi-error fixture did not fail") &&
         expect(first_result.diagnostics()->serialize() == expected,
                "first exact diagnostic bytes differ") &&
         expect(second_result.diagnostics()->serialize() == expected,
                "reordered exact diagnostic bytes differ");
}

/**
 * @brief Capture locale-independent construction outcomes for non-ASCII input bytes.
 * @return Acceptance of one UTF-8 identity and diagnostic.
 * @failure The fixture itself cannot fail; rejected construction is represented as false.
 */
[[nodiscard]] std::array<bool, 2U> locale_sensitive_outcomes() {
  constexpr std::string_view utf8_identity{"id.\xC4\x80"};
  return {
      Identity::create(utf8_identity).has_value(),
      Diagnostic::create({DiagnosticCode::required_field, DiagnosticSeverity::error,
                          ValidationPhase::item, utf8_identity, "reason", "correction"})
          .has_value(),
  };
}

/** @return true when validated construction is identical across caller C locales. */
[[nodiscard]] bool test_locale_independent_validation() {
  const char* initial_name = std::setlocale(LC_CTYPE, nullptr);
  const std::string initial = initial_name == nullptr ? "C" : initial_name;
  if (!expect(std::setlocale(LC_CTYPE, "C") != nullptr, "C locale is unavailable")) {
    return false;
  }
  const auto baseline = locale_sensitive_outcomes();
  constexpr std::array<std::string_view, 4U> alternatives{
      "en_US.iso88591", "en_US.UTF-8", "C.UTF-8", "C.utf8"};
  bool compared = false;
  bool stable = true;
  for (const std::string_view locale : alternatives) {
    if (std::setlocale(LC_CTYPE, locale.data()) != nullptr) {
      compared = true;
      stable = stable && locale_sensitive_outcomes() == baseline;
    }
  }
  static_cast<void>(std::setlocale(LC_CTYPE, initial.c_str()));
  return expect(compared, "no non-C comparison locale is available") &&
         expect(baseline == std::array<bool, 2U>{true, true},
                "non-ASCII bytes do not have the declared byte-oriented outcome") &&
         expect(stable, "validated construction changed with the caller locale");
}

}  // namespace

/** @return Zero when every negative fixture passes, otherwise one. */
int main() {
  const bool passed = test_invalid_direction_table() && test_contract_field_boundaries() &&
                      test_item_field_boundaries() && test_diagnostic_boundaries_and_codes() &&
                      test_exact_multi_error_sequence() && test_locale_independent_validation();
  return passed ? 0 : 1;
}

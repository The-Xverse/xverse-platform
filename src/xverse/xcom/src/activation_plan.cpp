/**
 * \file activation_plan.cpp
 * \brief Bounded X-COM activation_plan implementation unit.
 * \ingroup xcom_xdl
 */

// Bounded, immutable C++ decoder for the canonical X-COM activation-plan v1 artifact.
//
// Implements the T019 units: bounded strict parse (U-01), closed shape/vocabulary (U-02),
// canonicalization + in-tree SHA-256 + independent version/digest verification (U-03),
// independent capability/cross-reference/status verification (U-04), bounded immutable model
// (U-05), and deterministic outcome classification (U-06).
//
// The unit is a pure function over caller-supplied bytes. It performs no filesystem, network, or
// subprocess access and retains no global state. Only the C++20 standard library and the admitted
// nlohmann/json header are used.

#include "xverse/xcom/activation_plan.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <initializer_list>
#include <set>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

namespace xverse::xcom::plan {
namespace {

using json = nlohmann::json;

// Closed constant vocabulary (detailed-design.md §2.2/§2.3).
constexpr std::string_view kPlanTarget = "xcom-plan";
constexpr std::string_view kPlanVersion = "1";
constexpr std::string_view kDigestAlgorithm = "sha256";
constexpr std::string_view kPlanDomainSeparator = "xverse.xcom.activation-plan.v1";
constexpr std::string_view kApiVersion = "xverse.io/xdl/v1alpha1";

constexpr std::string_view kCodeInput = "XCOM-DECODE-INPUT";
constexpr std::string_view kCodeShape = "XCOM-DECODE-SHAPE";
constexpr std::string_view kCodeVersion = "XCOM-DECODE-VERSION";
constexpr std::string_view kCodeDigest = "XCOM-DECODE-DIGEST";
constexpr std::string_view kCodeCapability = "XCOM-DECODE-CAPABILITY";
constexpr std::string_view kCodeReference = "XCOM-DECODE-REFERENCE";
constexpr std::string_view kCodeUnresolved = "XCOM-DECODE-UNRESOLVED";
constexpr std::string_view kCodeBound = "XCOM-DECODE-BOUND";
constexpr std::string_view kCodeUnknown = "XCOM-DECODE-UNKNOWN";

/// Closed top-level member set of activation-plan v1 (drift-guarded against the T017 schema).
constexpr std::string_view kRequiredMembers[] = {
    "planVersion", "digest",     "generator",        "provenance", "contracts",
    "endpoints",   "routes",     "providers",        "policies",   "observationPoints",
    "stimulation", "clockDomains", "activationOrder", "diagnostics", "status",
    "inputResolution"};

DecodeOutcome outcome_for_code(std::string_view code) {
  if (code == kCodeBound || code == kCodeUnknown) {
    return DecodeOutcome::failed;
  }
  if (code.empty()) {
    return DecodeOutcome::accepted;
  }
  return DecodeOutcome::rejected;
}

bool set_error(DecodeError& err, std::string_view code, std::string_view target,
               std::string_view message) {
  if (err.code.empty()) {
    err.code = std::string(code);
    err.target_id = std::string(target);
    err.message = std::string(message);
  }
  return false;
}

bool fail_input(DecodeError& err, std::string_view message) {
  return set_error(err, kCodeInput, kPlanTarget, message);
}

bool fail_shape(DecodeError& err, std::string_view target, std::string_view message) {
  return set_error(err, kCodeShape, target, message);
}

bool fail_bound(DecodeError& err, std::string_view message) {
  return set_error(err, kCodeBound, kPlanTarget, message);
}

DecodeResult result_from_error(const DecodeError& err) {
  DecodeResult result;
  result.outcome = outcome_for_code(err.code);
  result.error = err;
  return result;
}

BytesResult bytes_from_error(const DecodeError& err) {
  BytesResult result;
  result.outcome = outcome_for_code(err.code);
  result.error = err;
  return result;
}

// --------------------------------------------------------------------------------------
// Pattern predicates (schema §$defs, detailed-design.md §2.4)
// --------------------------------------------------------------------------------------

bool is_lower_alpha(char c) { return c >= 'a' && c <= 'z'; }
bool is_digit(char c) { return c >= '0' && c <= '9'; }

int decimal(std::string_view value, std::size_t offset, std::size_t count) {
  if (offset + count > value.size()) {
    return -1;
  }
  int result = 0;
  for (std::size_t index = offset; index < offset + count; ++index) {
    if (!is_digit(value[index])) {
      return -1;
    }
    result = result * 10 + (value[index] - '0');
  }
  return result;
}

bool valid_rfc3339(std::string_view value) {
  if (value.size() < 20 || value[4] != '-' || value[7] != '-' ||
      (value[10] != 'T' && value[10] != 't') || value[13] != ':' || value[16] != ':') {
    return false;
  }
  const int year = decimal(value, 0, 4);
  const int month = decimal(value, 5, 2);
  const int day = decimal(value, 8, 2);
  const int hour = decimal(value, 11, 2);
  const int minute = decimal(value, 14, 2);
  const int second = decimal(value, 17, 2);
  if (year < 1 || month < 1 || month > 12 || hour < 0 || hour > 23 ||
      minute < 0 || minute > 59 || second < 0 || second > 59) {
    return false;
  }
  const bool leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
  const int days[] = {0, 31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
  if (day < 1 || day > days[month]) {
    return false;
  }
  std::size_t position = 19;
  if (position < value.size() && value[position] == '.') {
    ++position;
    const std::size_t fraction_start = position;
    while (position < value.size() && is_digit(value[position])) {
      ++position;
    }
    if (position == fraction_start) {
      return false;
    }
  }
  if (position + 1 == value.size() && (value[position] == 'Z' || value[position] == 'z')) {
    return true;
  }
  return position + 6 == value.size() && (value[position] == '+' || value[position] == '-') &&
         value[position + 3] == ':' && decimal(value, position + 1, 2) <= 23 &&
         decimal(value, position + 1, 2) >= 0 && decimal(value, position + 4, 2) <= 59 &&
         decimal(value, position + 4, 2) >= 0;
}
bool is_lower_alnum(char c) { return is_lower_alpha(c) || is_digit(c); }
bool is_upper_alnum_dash(char c) {
  return (c >= 'A' && c <= 'Z') || is_digit(c) || c == '-';
}

bool is_identifier(const std::string& value) {
  if (value.empty() || value.size() > 127) {
    return false;
  }
  if (!is_lower_alpha(value[0])) {
    return false;
  }
  std::size_t index = 1;
  while (index < value.size()) {
    const char c = value[index];
    if (is_lower_alnum(c)) {
      ++index;
      continue;
    }
    if (c != '.' && c != '-') {
      return false;
    }
    ++index;
    if (index >= value.size() || !is_lower_alnum(value[index])) {
      return false;
    }
  }
  return true;
}

bool is_version(const std::string& value) {
  std::size_t index = 0;
  auto digits = [&value, &index]() {
    const std::size_t start = index;
    while (index < value.size() && is_digit(value[index])) {
      ++index;
    }
    return index > start;
  };
  if (!digits()) {
    return false;
  }
  if (index >= value.size() || value[index] != '.') {
    return false;
  }
  ++index;
  if (!digits()) {
    return false;
  }
  if (index == value.size()) {
    return true;
  }
  if (value[index] != '.') {
    return false;
  }
  ++index;
  return digits() && index == value.size();
}

bool is_hex64(const std::string& value) {
  if (value.size() != 64) {
    return false;
  }
  for (char c : value) {
    const bool lower_hex = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
    if (!lower_hex) {
      return false;
    }
  }
  return true;
}

bool is_generator_task(const std::string& value) {
  if (value.size() != 4 || value[0] != 'T') {
    return false;
  }
  for (std::size_t i = 1; i < 4; ++i) {
    if (!is_digit(value[i])) {
      return false;
    }
  }
  return true;
}

bool is_diagnostic_code(const std::string& value) {
  if (value.size() < 8 || value.size() > 69) {
    return false;
  }
  if (value.compare(0, 5, "XCOM-") != 0) {
    return false;
  }
  for (std::size_t i = 5; i < value.size(); ++i) {
    if (!is_upper_alnum_dash(value[i])) {
      return false;
    }
  }
  return true;
}

// --------------------------------------------------------------------------------------
// SHA-256 (FIPS 180-4), implemented in-tree so no cryptographic dependency is added.
// --------------------------------------------------------------------------------------

constexpr std::uint32_t kSha256K[64] = {
    0x428a2f98u, 0x71374491u, 0xb5c0fbcfu, 0xe9b5dba5u, 0x3956c25bu, 0x59f111f1u, 0x923f82a4u,
    0xab1c5ed5u, 0xd807aa98u, 0x12835b01u, 0x243185beu, 0x550c7dc3u, 0x72be5d74u, 0x80deb1feu,
    0x9bdc06a7u, 0xc19bf174u, 0xe49b69c1u, 0xefbe4786u, 0x0fc19dc6u, 0x240ca1ccu, 0x2de92c6fu,
    0x4a7484aau, 0x5cb0a9dcu, 0x76f988dau, 0x983e5152u, 0xa831c66du, 0xb00327c8u, 0xbf597fc7u,
    0xc6e00bf3u, 0xd5a79147u, 0x06ca6351u, 0x14292967u, 0x27b70a85u, 0x2e1b2138u, 0x4d2c6dfcu,
    0x53380d13u, 0x650a7354u, 0x766a0abbu, 0x81c2c92eu, 0x92722c85u, 0xa2bfe8a1u, 0xa81a664bu,
    0xc24b8b70u, 0xc76c51a3u, 0xd192e819u, 0xd6990624u, 0xf40e3585u, 0x106aa070u, 0x19a4c116u,
    0x1e376c08u, 0x2748774cu, 0x34b0bcb5u, 0x391c0cb3u, 0x4ed8aa4au, 0x5b9cca4fu, 0x682e6ff3u,
    0x748f82eeu, 0x78a5636fu, 0x84c87814u, 0x8cc70208u, 0x90befffau, 0xa4506cebu, 0xbef9a3f7u,
    0xc67178f2u};

std::uint32_t rotr(std::uint32_t value, std::uint32_t shift) {
  return (value >> shift) | (value << (32u - shift));
}

std::array<std::uint8_t, 32> sha256_bytes(std::string_view data) {
  std::uint32_t h[8] = {0x6a09e667u, 0xbb67ae85u, 0x3c6ef372u, 0xa54ff53au,
                        0x510e527fu, 0x9b05688cu, 0x1f83d9abu, 0x5be0cd19u};

  std::vector<std::uint8_t> message(data.begin(), data.end());
  const std::uint64_t bit_length = static_cast<std::uint64_t>(message.size()) * 8u;
  message.push_back(0x80u);
  while (message.size() % 64u != 56u) {
    message.push_back(0x00u);
  }
  for (int shift = 56; shift >= 0; shift -= 8) {
    message.push_back(static_cast<std::uint8_t>((bit_length >> shift) & 0xffu));
  }

  for (std::size_t offset = 0; offset < message.size(); offset += 64u) {
    std::uint32_t w[64] = {};
    for (std::size_t i = 0; i < 16; ++i) {
      const std::size_t base = offset + i * 4u;
      w[i] = (static_cast<std::uint32_t>(message[base]) << 24u) |
             (static_cast<std::uint32_t>(message[base + 1]) << 16u) |
             (static_cast<std::uint32_t>(message[base + 2]) << 8u) |
             static_cast<std::uint32_t>(message[base + 3]);
    }
    for (std::size_t i = 16; i < 64; ++i) {
      const std::uint32_t s0 = rotr(w[i - 15], 7) ^ rotr(w[i - 15], 18) ^ (w[i - 15] >> 3);
      const std::uint32_t s1 = rotr(w[i - 2], 17) ^ rotr(w[i - 2], 19) ^ (w[i - 2] >> 10);
      w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    std::uint32_t a = h[0];
    std::uint32_t b = h[1];
    std::uint32_t c = h[2];
    std::uint32_t d = h[3];
    std::uint32_t e = h[4];
    std::uint32_t f = h[5];
    std::uint32_t g = h[6];
    std::uint32_t hh = h[7];
    for (std::size_t i = 0; i < 64; ++i) {
      const std::uint32_t s1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25);
      const std::uint32_t ch = (e & f) ^ ((~e) & g);
      const std::uint32_t temp1 = hh + s1 + ch + kSha256K[i] + w[i];
      const std::uint32_t s0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22);
      const std::uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
      const std::uint32_t temp2 = s0 + maj;
      hh = g;
      g = f;
      f = e;
      e = d + temp1;
      d = c;
      c = b;
      b = a;
      a = temp1 + temp2;
    }
    h[0] += a;
    h[1] += b;
    h[2] += c;
    h[3] += d;
    h[4] += e;
    h[5] += f;
    h[6] += g;
    h[7] += hh;
  }

  std::array<std::uint8_t, 32> digest{};
  for (std::size_t i = 0; i < 8; ++i) {
    digest[i * 4u] = static_cast<std::uint8_t>((h[i] >> 24u) & 0xffu);
    digest[i * 4u + 1u] = static_cast<std::uint8_t>((h[i] >> 16u) & 0xffu);
    digest[i * 4u + 2u] = static_cast<std::uint8_t>((h[i] >> 8u) & 0xffu);
    digest[i * 4u + 3u] = static_cast<std::uint8_t>(h[i] & 0xffu);
  }
  return digest;
}

// --------------------------------------------------------------------------------------
// Canonical serialization (T017 rule reproduced independently)
// --------------------------------------------------------------------------------------

void append_json_string(const std::string& value, std::string& out) {
  out.push_back('"');
  for (char raw : value) {
    const unsigned char c = static_cast<unsigned char>(raw);
    switch (c) {
      case '"':
        out.append("\\\"");
        break;
      case '\\':
        out.append("\\\\");
        break;
      case '\b':
        out.append("\\b");
        break;
      case '\f':
        out.append("\\f");
        break;
      case '\n':
        out.append("\\n");
        break;
      case '\r':
        out.append("\\r");
        break;
      case '\t':
        out.append("\\t");
        break;
      default:
        if (c < 0x20u) {
          static constexpr char kHex[] = "0123456789abcdef";
          out.append("\\u00");
          out.push_back(kHex[(c >> 4u) & 0x0fu]);
          out.push_back(kHex[c & 0x0fu]);
        } else {
          out.push_back(raw);
        }
        break;
    }
  }
  out.push_back('"');
}

bool canonical_bytes(const json& value, std::string& out) {
  if (value.is_object()) {
    std::vector<std::string> keys;
    keys.reserve(value.size());
    for (auto& item : value.items()) {
      keys.push_back(item.key());
    }
    std::sort(keys.begin(), keys.end(), std::less<std::string>());
    out.push_back('{');
    bool first = true;
    for (auto& key : keys) {
      if (!first) {
        out.push_back(',');
      }
      first = false;
      append_json_string(key, out);
      out.push_back(':');
      if (!canonical_bytes(value.at(key), out)) {
        return false;
      }
    }
    out.push_back('}');
    return true;
  }
  if (value.is_array()) {
    out.push_back('[');
    bool first = true;
    for (auto& element : value) {
      if (!first) {
        out.push_back(',');
      }
      first = false;
      if (!canonical_bytes(element, out)) {
        return false;
      }
    }
    out.push_back(']');
    return true;
  }
  if (value.is_string()) {
    append_json_string(value.get_ref<const std::string&>(), out);
    return true;
  }
  if (value.is_boolean()) {
    out.append(value.get<bool>() ? "true" : "false");
    return true;
  }
  if (value.is_null()) {
    out.append("null");
    return true;
  }
  if (value.is_number_unsigned()) {
    out.append(std::to_string(value.get<std::uint64_t>()));
    return true;
  }
  if (value.is_number_integer()) {
    out.append(std::to_string(value.get<std::int64_t>()));
    return true;
  }
  if (value.is_number_float()) {
    const double number = value.get<double>();
    if (!std::isfinite(number) || std::floor(number) != number ||
        number < -9223372036854775808.0 || number >= 9223372036854775808.0) {
      return false;
    }
    out.append(std::to_string(static_cast<std::int64_t>(number)));
    return true;
  }
  return false;
}

// --------------------------------------------------------------------------------------
// Bounded strict parse (U-01)
// --------------------------------------------------------------------------------------

class BoundedSax final : public nlohmann::json_sax<json> {
 public:
  explicit BoundedSax(const DecodeLimits& limits) : limits_(limits) {}

  bool null() override { return add_value(json(nullptr)); }

  bool boolean(bool value) override { return add_value(json(value)); }

  bool number_integer(number_integer_t value) override {
    return add_value(json(static_cast<std::int64_t>(value)));
  }

  bool number_unsigned(number_unsigned_t value) override {
    return add_value(json(static_cast<std::uint64_t>(value)));
  }

  bool number_float(number_float_t value, const string_t&) override {
    if (!std::isfinite(value)) {
      return fail(kCodeInput, kPlanTarget, "non-finite number");
    }
    if (std::floor(value) == value) {
      if (value >= -9223372036854775808.0 && value < 9223372036854775808.0) {
        return add_value(json(static_cast<std::int64_t>(value)));
      }
      if (value >= 0.0 && value < 18446744073709551616.0) {
        return add_value(json(static_cast<std::uint64_t>(value)));
      }
      // An integral token outside the int64/uint64 range is rejected rather than silently retained
      // as a double (detailed-design.md §4 step 3, §12).
      return fail(kCodeInput, kPlanTarget, "integral number outside the representable range");
    }
    return add_value(json(value));
  }

  bool string(string_t& value) override {
    if (value.size() > limits_.max_string_length) {
      return fail(kCodeShape, kPlanTarget, "string exceeds the declared bound");
    }
    return add_value(json(value));
  }

  bool binary(binary_t&) override { return fail(kCodeInput, kPlanTarget, "binary is not accepted"); }

  bool start_object(std::size_t) override { return begin_container(true); }

  bool start_array(std::size_t) override { return begin_container(false); }

  bool key(string_t& value) override {
    if (stack_.empty() || !stack_.back()->is_object()) {
      return fail(kCodeInput, kPlanTarget, "unexpected object key");
    }
    if (value.size() > limits_.max_string_length) {
      return fail(kCodeShape, kPlanTarget, "object key exceeds the declared bound");
    }
    if (!keys_.back().insert(value).second) {
      return fail(kCodeInput, kPlanTarget, "duplicate object member");
    }
    key_ = value;
    return true;
  }

  bool end_object() override {
    if (stack_.empty() || !stack_.back()->is_object() || keys_.empty()) {
      return fail(kCodeInput, kPlanTarget, "unbalanced object");
    }
    stack_.pop_back();
    keys_.pop_back();
    return true;
  }

  bool end_array() override {
    if (stack_.empty() || !stack_.back()->is_array()) {
      return fail(kCodeInput, kPlanTarget, "unbalanced array");
    }
    stack_.pop_back();
    return true;
  }

  bool parse_error(std::size_t, const std::string&, const nlohmann::detail::exception&) override {
    if (!failed_) {
      fail(kCodeInput, kPlanTarget, "malformed JSON");
    }
    return false;
  }

  bool failed() const noexcept { return failed_; }
  const DecodeError& error() const noexcept { return error_; }
  bool has_root() const noexcept { return root_ != nullptr; }
  json take_root() { return std::move(root_owner_); }

 private:
  bool fail(std::string_view code, std::string_view target, std::string_view message) {
    if (!failed_) {
      failed_ = true;
      error_.code = std::string(code);
      error_.target_id = std::string(target);
      error_.message = std::string(message);
    }
    return false;
  }

  bool check_bounds() {
    if (stack_.size() + 1u > limits_.max_depth) {
      return fail(kCodeBound, kPlanTarget, "nesting depth exceeds the declared bound");
    }
    if (++node_count_ > limits_.max_nodes) {
      return fail(kCodeBound, kPlanTarget, "node count exceeds the declared bound");
    }
    return true;
  }

  bool begin_container(bool is_object) {
    if (failed_ || !check_bounds()) {
      return false;
    }
    json* node = nullptr;
    if (stack_.empty()) {
      if (root_ != nullptr) {
        return fail(kCodeInput, kPlanTarget, "multiple root values");
      }
      root_owner_ = is_object ? json::object() : json::array();
      node = &root_owner_;
      root_ = node;
    } else {
      json* parent = stack_.back();
      if (parent->is_object()) {
        auto inserted = parent->emplace(key_, is_object ? json::object() : json::array());
        node = &(*inserted.first);
      } else {
        parent->push_back(is_object ? json::object() : json::array());
        node = &parent->back();
      }
    }
    stack_.push_back(node);
    if (is_object) {
      keys_.emplace_back();
    }
    return true;
  }

  bool add_value(json value) {
    if (failed_ || !check_bounds()) {
      return false;
    }
    if (stack_.empty()) {
      if (root_ != nullptr) {
        return fail(kCodeInput, kPlanTarget, "multiple root values");
      }
      root_owner_ = std::move(value);
      root_ = &root_owner_;
      return true;
    }
    json* parent = stack_.back();
    if (parent->is_object()) {
      (*parent)[key_] = std::move(value);
    } else {
      parent->push_back(std::move(value));
    }
    return true;
  }

  const DecodeLimits& limits_;
  json root_owner_;
  json* root_ = nullptr;
  std::vector<json*> stack_;
  std::vector<std::set<std::string>> keys_;
  std::string key_;
  std::size_t node_count_ = 0;
  bool failed_ = false;
  DecodeError error_;
};

bool parse_bounded(std::string_view bytes, const DecodeLimits& limits, json& out,
                   DecodeError& err) {
  if (!is_valid(limits)) {
    return set_error(err, kCodeUnknown, kPlanTarget, "invalid decode limits");
  }
  if (bytes.size() > limits.max_bytes) {
    return fail_bound(err, "plan bytes exceed the declared bound");
  }
  BoundedSax handler(limits);
  const char* first = bytes.data();
  const char* last = bytes.data() + bytes.size();
  const bool parsed = json::sax_parse(first, last, &handler, nlohmann::json::input_format_t::json,
                                      /*strict=*/true, /*ignore_comments=*/false);
  if (handler.failed()) {
    err = handler.error();
    return false;
  }
  if (!parsed || !handler.has_root()) {
    return fail_input(err, "malformed JSON");
  }
  out = handler.take_root();
  if (!out.is_object()) {
    return fail_input(err, "plan root must be an object");
  }
  return true;
}

// --------------------------------------------------------------------------------------
// Closed shape, vocabulary, identifiers, and order (U-02)
// --------------------------------------------------------------------------------------

bool check_object(const json& node, std::string_view target, DecodeError& err,
                  std::initializer_list<std::string_view> required,
                  std::initializer_list<std::string_view> optional = {}) {
  if (!node.is_object()) {
    return fail_shape(err, target, "must be an object");
  }
  for (auto& item : node.items()) {
    bool known = false;
    for (std::string_view name : required) {
      if (item.key() == name) {
        known = true;
      }
    }
    for (std::string_view name : optional) {
      if (item.key() == name) {
        known = true;
      }
    }
    if (!known) {
      return fail_shape(err, target, "unknown member");
    }
  }
  for (std::string_view name : required) {
    if (!node.contains(std::string(name))) {
      return fail_shape(err, target, "missing required member");
    }
  }
  return true;
}

bool require_string(const json& node, std::string_view target, DecodeError& err) {
  if (!node.is_string()) {
    return fail_shape(err, target, "must be a string");
  }
  return true;
}

bool require_identifier(const json& node, std::string_view target, DecodeError& err) {
  if (!node.is_string() || !is_identifier(node.get_ref<const std::string&>())) {
    return fail_shape(err, target, "must be a declared identifier");
  }
  return true;
}

bool require_version(const json& node, std::string_view target, DecodeError& err) {
  if (!node.is_string() || !is_version(node.get_ref<const std::string&>())) {
    return fail_shape(err, target, "must be a declared version");
  }
  return true;
}

bool require_enum(const json& node, std::string_view target, DecodeError& err,
                  std::initializer_list<std::string_view> values) {
  if (!node.is_string()) {
    return fail_shape(err, target, "must be a vocabulary token");
  }
  const std::string& token = node.get_ref<const std::string&>();
  for (std::string_view value : values) {
    if (token == value) {
      return true;
    }
  }
  return fail_shape(err, target, "violates the closed vocabulary");
}

// Structural check of an embedded digest object: exactly the members {algorithm, value}, both
// strings. Only the top-level recorded `digest` is checked structurally here; its algorithm/hex
// form is classified at the version/digest step so a malformed recorded digest is
// `XCOM-DECODE-DIGEST` rather than `XCOM-DECODE-SHAPE` (verification-plan.md §4.3, NEG-D10).
bool require_digest_members(const json& node, std::string_view target, DecodeError& err) {
  if (!check_object(node, target, err, {"algorithm", "value"})) {
    return false;
  }
  if (!node.at("algorithm").is_string() || !node.at("value").is_string()) {
    return fail_shape(err, target, "digest members must be strings");
  }
  return true;
}

// Closed digest sub-schema (PLAN_SCHEMA `$defs/digest`; detailed-design.md §2.4/§5): the members
// above plus algorithm == "sha256" and value =~ ^[0-9a-f]{64}$. Enforced for every embedded digest
// (`provenance.graphDigest` and each `provenance.resources[].sourceDigest`) so a schema-invalid
// nested digest fails closed with `XCOM-DECODE-SHAPE`; the top-level recorded digest's algorithm
// and hex form are enforced at the version/digest step (see `require_digest_members`).
bool require_digest(const json& node, std::string_view target, DecodeError& err) {
  if (!require_digest_members(node, target, err)) {
    return false;
  }
  if (node.at("algorithm").get<std::string>() != kDigestAlgorithm) {
    return fail_shape(err, target, "digest algorithm violates the closed vocabulary");
  }
  if (!is_hex64(node.at("value").get<std::string>())) {
    return fail_shape(err, target, "digest value must be 64 lowercase hex digits");
  }
  return true;
}

bool require_integer_range(const json& node, std::string_view target, DecodeError& err,
                           std::int64_t low, std::int64_t high) {
  std::int64_t value = 0;
  if (node.is_number_unsigned()) {
    const std::uint64_t raw = node.get<std::uint64_t>();
    if (raw > static_cast<std::uint64_t>(high)) {
      return fail_shape(err, target, "integer is outside the declared range");
    }
    value = static_cast<std::int64_t>(raw);
  } else if (node.is_number_integer()) {
    value = node.get<std::int64_t>();
  } else {
    return fail_shape(err, target, "must be an integer");
  }
  if (value < low || value > high) {
    return fail_shape(err, target, "integer is outside the declared range");
  }
  return true;
}

bool require_unique_identifiers(const json& node, std::string_view target, DecodeError& err,
                                bool require_non_empty) {
  if (!node.is_array()) {
    return fail_shape(err, target, "must be an array");
  }
  if (require_non_empty && node.empty()) {
    return fail_shape(err, target, "must not be empty");
  }
  std::set<std::string> seen;
  for (auto& element : node) {
    if (!require_identifier(element, target, err)) {
      return false;
    }
    if (!seen.insert(element.get<std::string>()).second) {
      return fail_shape(err, target, "carries a duplicate entry");
    }
  }
  return true;
}

int compare_strings(const std::string& left, const std::string& right) {
  if (left < right) {
    return -1;
  }
  if (right < left) {
    return 1;
  }
  return 0;
}

int compare_resources(const json& left, const json& right) {
  const char* fields[] = {"apiVersion", "kind", "namespace", "name"};
  for (const char* field : fields) {
    const int order = compare_strings(left.at(field).get<std::string>(), right.at(field).get<std::string>());
    if (order != 0) {
      return order;
    }
  }
  const bool left_has = left.contains("version");
  const bool right_has = right.contains("version");
  if (left_has != right_has) {
    return left_has ? 1 : -1;  // an absent optional member sorts first
  }
  if (!left_has) {
    return 0;
  }
  return compare_strings(left.at("version").get<std::string>(), right.at("version").get<std::string>());
}

bool check_key_order(const json& array, std::string_view target, DecodeError& err,
                     const std::function<int(const json&, const json&)>& compare) {
  for (std::size_t i = 1; i < array.size(); ++i) {
    if (compare(array[i - 1], array[i]) >= 0) {
      return fail_shape(err, target, "collection is not strictly ordered or has a duplicate key");
    }
  }
  return true;
}

bool check_digest_shape(const json& node, std::string_view target, DecodeError& err) {
  return require_digest(node, target, err);
}

bool validate_shape(const json& plan, DecodeError& err) {
  // Root closed shape: exactly the sixteen declared members.
  if (!plan.is_object()) {
    return fail_shape(err, kPlanTarget, "plan must be an object");
  }
  for (auto& item : plan.items()) {
    bool known = false;
    for (std::string_view name : kRequiredMembers) {
      if (item.key() == name) {
        known = true;
      }
    }
    if (!known) {
      return fail_shape(err, kPlanTarget, "unknown top-level member");
    }
  }
  for (std::string_view name : kRequiredMembers) {
    if (!plan.contains(std::string(name))) {
      return fail_shape(err, kPlanTarget, "missing required top-level member");
    }
  }

  if (!require_string(plan.at("planVersion"), kPlanTarget, err)) {
    return false;
  }
  if (!require_digest_members(plan.at("digest"), kPlanTarget, err)) {
    return false;
  }

  const json& generator = plan.at("generator");
  if (!check_object(generator, "generator", err, {"task", "version"})) {
    return false;
  }
  if (!generator.at("task").is_string() || !is_generator_task(generator.at("task").get<std::string>())) {
    return fail_shape(err, "generator", "task must match Tnnn");
  }
  if (!require_version(generator.at("version"), "generator", err)) {
    return false;
  }

  const json& provenance = plan.at("provenance");
  if (!check_object(provenance, "provenance", err, {"generatedAt", "graphDigest", "resources"})) {
    return false;
  }
  if (!require_string(provenance.at("generatedAt"), "provenance", err) ||
      !valid_rfc3339(provenance.at("generatedAt").get_ref<const std::string&>())) {
    if (err.code.empty()) {
      return fail_shape(err, "provenance", "generatedAt must be a real RFC 3339 date-time");
    }
    return false;
  }
  if (!check_digest_shape(provenance.at("graphDigest"), "provenance", err)) {
    return false;
  }
  const json& resources = provenance.at("resources");
  if (!resources.is_array() || resources.empty()) {
    return fail_shape(err, "provenance", "resources must be a non-empty array");
  }
  for (auto& resource : resources) {
    if (!check_object(resource, "provenance", err,
                      {"apiVersion", "kind", "namespace", "name", "sourceDigest"}, {"version"})) {
      return false;
    }
    if (!resource.at("apiVersion").is_string() ||
        resource.at("apiVersion").get<std::string>() != kApiVersion) {
      return fail_shape(err, "provenance", "apiVersion must be the declared const");
    }
    if (!require_enum(resource.at("kind"), "provenance", err, {"Component", "Deployment", "Scenario"})) {
      return false;
    }
    if (!require_identifier(resource.at("namespace"), "provenance", err) ||
        !require_identifier(resource.at("name"), "provenance", err)) {
      return false;
    }
    if (resource.contains("version") && !require_version(resource.at("version"), "provenance", err)) {
      return false;
    }
    if (!check_digest_shape(resource.at("sourceDigest"), "provenance", err)) {
      return false;
    }
  }
  if (!check_key_order(resources, "provenance", err, compare_resources)) {
    return false;
  }

  const json& contracts = plan.at("contracts");
  if (!contracts.is_array()) {
    return fail_shape(err, "contracts", "must be an array");
  }
  for (auto& contract : contracts) {
    if (!check_object(contract, "contracts", err, {"contractId", "schemaId", "schemaVersion"})) {
      return false;
    }
    if (!require_identifier(contract.at("contractId"), "contracts", err) ||
        !require_identifier(contract.at("schemaId"), "contracts", err) ||
        !require_version(contract.at("schemaVersion"), "contracts", err)) {
      return false;
    }
  }
  if (!check_key_order(contracts, "contracts", err,
                       [](const json& a, const json& b) {
                         return compare_strings(a.at("contractId").get<std::string>(),
                                                b.at("contractId").get<std::string>());
                       })) {
    return false;
  }

  const json& endpoints = plan.at("endpoints");
  if (!endpoints.is_array()) {
    return fail_shape(err, "endpoints", "must be an array");
  }
  for (auto& endpoint : endpoints) {
    if (!check_object(endpoint, "endpoints", err, {"endpointId", "role"})) {
      return false;
    }
    if (!require_identifier(endpoint.at("endpointId"), "endpoints", err) ||
        !require_enum(endpoint.at("role"), "endpoints", err, {"initiator", "responder", "observer", "tool"})) {
      return false;
    }
  }
  if (!check_key_order(endpoints, "endpoints", err,
                       [](const json& a, const json& b) {
                         return compare_strings(a.at("endpointId").get<std::string>(),
                                                b.at("endpointId").get<std::string>());
                       })) {
    return false;
  }

  const json& routes = plan.at("routes");
  if (!routes.is_array()) {
    return fail_shape(err, "routes", "must be an array");
  }
  for (auto& route : routes) {
    if (!check_object(route, "routes", err, {"routeId", "from", "to", "contractId"})) {
      return false;
    }
    if (!require_identifier(route.at("routeId"), "routes", err) ||
        !require_identifier(route.at("from"), "routes", err) ||
        !require_identifier(route.at("to"), "routes", err) ||
        !require_identifier(route.at("contractId"), "routes", err)) {
      return false;
    }
  }
  if (!check_key_order(routes, "routes", err,
                       [](const json& a, const json& b) {
                         return compare_strings(a.at("routeId").get<std::string>(),
                                                b.at("routeId").get<std::string>());
                       })) {
    return false;
  }

  const json& providers = plan.at("providers");
  if (!providers.is_array()) {
    return fail_shape(err, "providers", "must be an array");
  }
  for (auto& provider : providers) {
    if (!check_object(provider, "providers", err,
                      {"providerId", "capabilities", "requiredCapabilities"})) {
      return false;
    }
    if (!require_identifier(provider.at("providerId"), "providers", err)) {
      return false;
    }
    if (!require_unique_identifiers(provider.at("capabilities"), "providers", err,
                                    /*require_non_empty=*/true)) {
      return false;
    }
    if (!require_unique_identifiers(provider.at("requiredCapabilities"), "providers", err,
                                    /*require_non_empty=*/false)) {
      return false;
    }
  }
  if (!check_key_order(providers, "providers", err,
                       [](const json& a, const json& b) {
                         return compare_strings(a.at("providerId").get<std::string>(),
                                                b.at("providerId").get<std::string>());
                       })) {
    return false;
  }

  const json& policies = plan.at("policies");
  if (!check_object(policies, "policies", err,
                    {"ordering", "reliability", "deadlineMs", "retry", "queueDepth", "overflow",
                     "backpressure"})) {
    return false;
  }
  if (!require_enum(policies.at("ordering"), "policies", err, {"fifo", "priority", "unordered"}) ||
      !require_enum(policies.at("reliability"), "policies", err,
                    {"at-most-once", "at-least-once", "exactly-once", "best-effort"}) ||
      !require_enum(policies.at("overflow"), "policies", err,
                    {"drop-oldest", "drop-newest", "coalesce", "lossless-backpressure", "reject",
                     "fail-closed"}) ||
      !require_enum(policies.at("backpressure"), "policies", err,
                    {"fail-closed", "reject", "lossless-backpressure"}) ||
      !require_integer_range(policies.at("deadlineMs"), "policies", err, 0, 600000) ||
      !require_integer_range(policies.at("retry"), "policies", err, 0, 64) ||
      !require_integer_range(policies.at("queueDepth"), "policies", err, 1, 65536)) {
    return false;
  }

  const json& observation_points = plan.at("observationPoints");
  if (!observation_points.is_array()) {
    return fail_shape(err, "observationPoints", "must be an array");
  }
  for (auto& tap : observation_points) {
    if (!check_object(tap, "observationPoints", err,
                      {"tapId", "routeId", "payloadAccess", "validityEffect"})) {
      return false;
    }
    if (!require_identifier(tap.at("tapId"), "observationPoints", err) ||
        !require_identifier(tap.at("routeId"), "observationPoints", err) ||
        !require_enum(tap.at("payloadAccess"), "observationPoints", err,
                      {"metadata-only", "allow-listed"}) ||
        !require_enum(tap.at("validityEffect"), "observationPoints", err,
                      {"none", "degrade-on-loss", "invalidate-on-loss"})) {
      return false;
    }
  }
  if (!check_key_order(observation_points, "observationPoints", err,
                       [](const json& a, const json& b) {
                         return compare_strings(a.at("tapId").get<std::string>(),
                                                b.at("tapId").get<std::string>());
                       })) {
    return false;
  }

  const json& stimulation = plan.at("stimulation");
  if (!check_object(stimulation, "stimulation", err, {"actions", "permitPolicyRefs"})) {
    return false;
  }
  if (!require_unique_identifiers(stimulation.at("actions"), "stimulation", err, false) ||
      !require_unique_identifiers(stimulation.at("permitPolicyRefs"), "stimulation", err, false)) {
    return false;
  }

  const json& clock_domains = plan.at("clockDomains");
  if (!clock_domains.is_array()) {
    return fail_shape(err, "clockDomains", "must be an array");
  }
  for (auto& domain : clock_domains) {
    if (!check_object(domain, "clockDomains", err, {"clockDomainId", "source"})) {
      return false;
    }
    if (!require_identifier(domain.at("clockDomainId"), "clockDomains", err) ||
        !require_enum(domain.at("source"), "clockDomains", err,
                      {"monotonic", "local-validation-clock", "unmapped"})) {
      return false;
    }
  }
  if (!check_key_order(clock_domains, "clockDomains", err,
                       [](const json& a, const json& b) {
                         return compare_strings(a.at("clockDomainId").get<std::string>(),
                                                b.at("clockDomainId").get<std::string>());
                       })) {
    return false;
  }

  const json& activation_order = plan.at("activationOrder");
  if (!require_unique_identifiers(activation_order, "activationOrder", err, /*require_non_empty=*/true)) {
    return false;
  }

  const json& diagnostics = plan.at("diagnostics");
  if (!diagnostics.is_array()) {
    return fail_shape(err, "diagnostics", "must be an array");
  }
  for (auto& diagnostic : diagnostics) {
    if (!check_object(diagnostic, "diagnostics", err, {"code", "severity", "targetId"})) {
      return false;
    }
    if (!diagnostic.at("code").is_string() ||
        !is_diagnostic_code(diagnostic.at("code").get<std::string>())) {
      return fail_shape(err, "diagnostics", "code must match the declared pattern");
    }
    if (!require_enum(diagnostic.at("severity"), "diagnostics", err, {"error", "warning", "info"}) ||
        !require_identifier(diagnostic.at("targetId"), "diagnostics", err)) {
      return false;
    }
  }
  if (!check_key_order(diagnostics, "diagnostics", err,
                       [](const json& a, const json& b) {
                         const int by_code = compare_strings(a.at("code").get<std::string>(),
                                                             b.at("code").get<std::string>());
                         if (by_code != 0) {
                           return by_code;
                         }
                         return compare_strings(a.at("targetId").get<std::string>(),
                                                b.at("targetId").get<std::string>());
                       })) {
    return false;
  }

  if (!require_enum(plan.at("status"), kPlanTarget, err, {"inspectable", "activatable"})) {
    return false;
  }

  const json& resolution = plan.at("inputResolution");
  if (!check_object(resolution, "inputResolution", err,
                    {"identity", "schema", "capability", "time", "ownership", "policy"})) {
    return false;
  }
  for (const char* member : {"identity", "schema", "capability", "time", "ownership", "policy"}) {
    if (!require_enum(resolution.at(member), "inputResolution", err, {"resolved", "unresolved"})) {
      return false;
    }
  }

  return true;
}

// --------------------------------------------------------------------------------------
// Capability, cross-reference, and status verification (U-04)
// --------------------------------------------------------------------------------------

bool validate_capability_and_references(const json& plan, DecodeError& err) {
  std::set<std::string> contract_ids;
  std::set<std::string> endpoint_ids;
  std::set<std::string> route_ids;

  for (auto& contract : plan.at("contracts")) {
    contract_ids.insert(contract.at("contractId").get<std::string>());
  }
  for (auto& endpoint : plan.at("endpoints")) {
    endpoint_ids.insert(endpoint.at("endpointId").get<std::string>());
  }
  for (auto& route : plan.at("routes")) {
    route_ids.insert(route.at("routeId").get<std::string>());
  }

  // The plan's own input-resolution states are the authority for whether a missing closure is a
  // defect. The accepted T018 producer records `capability = "unresolved"` when a graph declares
  // routes but selects no provider (or a provider is capability-insufficient) and `schema =
  // "unresolved"` when a route references an undeclared contract, emitting an `inspectable` plan.
  // Such a plan honestly declares the missing closure and is accepted as a non-activatable value
  // (T019-STK-003 AC-3); only a plan that claims the corresponding state `resolved` while
  // violating closure is rejected (detailed-design.md §7).
  const json& resolution = plan.at("inputResolution");
  const bool capability_resolved = resolution.at("capability").get<std::string>() == "resolved";
  const bool schema_resolved = resolution.at("schema").get<std::string>() == "resolved";
  const bool identity_resolved = resolution.at("identity").get<std::string>() == "resolved";

  if (capability_resolved) {
    if (!plan.at("routes").empty() && plan.at("providers").empty()) {
      return set_error(err, kCodeCapability, kPlanTarget,
                       "a plan declaring routes must select at least one provider");
    }
    for (auto& provider : plan.at("providers")) {
      const std::string provider_id = provider.at("providerId").get<std::string>();
      std::set<std::string> declared;
      for (auto& capability : provider.at("capabilities")) {
        declared.insert(capability.get<std::string>());
      }
      for (auto& required : provider.at("requiredCapabilities")) {
        if (declared.count(required.get<std::string>()) == 0) {
          return set_error(err, kCodeCapability, provider_id,
                           "required capability is not declared by the provider");
        }
      }
    }
  }

  if (schema_resolved) {
    for (auto& route : plan.at("routes")) {
      const std::string route_id = route.at("routeId").get<std::string>();
      if (contract_ids.count(route.at("contractId").get<std::string>()) == 0) {
        return set_error(err, kCodeReference, route_id, "route references an undeclared contract");
      }
    }
    for (auto& tap : plan.at("observationPoints")) {
      if (route_ids.count(tap.at("routeId").get<std::string>()) == 0) {
        return set_error(err, kCodeReference, tap.at("tapId").get<std::string>(),
                         "observation point references an undeclared route");
      }
    }
  }

  if (identity_resolved) {
    for (auto& route : plan.at("routes")) {
      const std::string route_id = route.at("routeId").get<std::string>();
      if (endpoint_ids.count(route.at("from").get<std::string>()) == 0 ||
          endpoint_ids.count(route.at("to").get<std::string>()) == 0) {
        return set_error(err, kCodeReference, route_id, "route references an undeclared endpoint");
      }
    }
    for (auto& entry : plan.at("activationOrder")) {
      const std::string& id = entry.get_ref<const std::string&>();
      if (endpoint_ids.count(id) == 0 && route_ids.count(id) == 0) {
        return set_error(err, kCodeReference, kPlanTarget,
                         "activation order names an undeclared identifier");
      }
    }
  }

  if (plan.at("status").get<std::string>() == "activatable") {
    for (const char* member : {"identity", "schema", "capability", "time", "ownership", "policy"}) {
      if (resolution.at(member).get<std::string>() != "resolved") {
        return set_error(err, kCodeUnresolved, kPlanTarget,
                         "an activatable plan requires six resolved input states");
      }
    }
  }

  return true;
}

// --------------------------------------------------------------------------------------
// Bounded immutable model (U-05)
// --------------------------------------------------------------------------------------

std::int64_t json_integer(const json& node) {
  if (node.is_number_unsigned()) {
    return static_cast<std::int64_t>(node.get<std::uint64_t>());
  }
  return node.get<std::int64_t>();
}

bool build_model(const json& plan, const DecodeLimits& limits, DecodeError& err,
                 ActivationPlan& out) {
  if (plan.at("provenance").at("resources").size() > limits.max_provenance_resources) {
    return fail_bound(err, "provenance resource count exceeds the declared cap");
  }
  if (plan.at("contracts").size() > limits.max_contracts) {
    return fail_bound(err, "contract count exceeds the declared cap");
  }
  if (plan.at("endpoints").size() > limits.max_endpoints) {
    return fail_bound(err, "endpoint count exceeds the declared cap");
  }
  if (plan.at("routes").size() > limits.max_routes) {
    return fail_bound(err, "route count exceeds the declared cap");
  }
  if (plan.at("providers").size() > limits.max_providers) {
    return fail_bound(err, "provider count exceeds the declared cap");
  }
  if (plan.at("observationPoints").size() > limits.max_observation_points) {
    return fail_bound(err, "observation point count exceeds the declared cap");
  }
  if (plan.at("clockDomains").size() > limits.max_clock_domains) {
    return fail_bound(err, "clock domain count exceeds the declared cap");
  }
  if (plan.at("diagnostics").size() > limits.max_diagnostics) {
    return fail_bound(err, "diagnostic count exceeds the declared cap");
  }
  if (plan.at("activationOrder").size() > limits.max_activation_order) {
    return fail_bound(err, "activation order count exceeds the declared cap");
  }

  out.plan_version = plan.at("planVersion").get<std::string>();
  out.digest.algorithm = plan.at("digest").at("algorithm").get<std::string>();
  out.digest.value = plan.at("digest").at("value").get<std::string>();
  out.generator_task = plan.at("generator").at("task").get<std::string>();
  out.generator_version = plan.at("generator").at("version").get<std::string>();

  const json& provenance = plan.at("provenance");
  out.provenance.generated_at = provenance.at("generatedAt").get<std::string>();
  out.provenance.graph_digest.algorithm = provenance.at("graphDigest").at("algorithm").get<std::string>();
  out.provenance.graph_digest.value = provenance.at("graphDigest").at("value").get<std::string>();
  out.provenance.resources.reserve(provenance.at("resources").size());
  for (auto& resource : provenance.at("resources")) {
    ResourceRef ref;
    ref.api_version = resource.at("apiVersion").get<std::string>();
    ref.kind = resource.at("kind").get<std::string>();
    ref.ns = resource.at("namespace").get<std::string>();
    ref.name = resource.at("name").get<std::string>();
    if (resource.contains("version")) {
      ref.version = resource.at("version").get<std::string>();
    }
    ref.source_digest.algorithm = resource.at("sourceDigest").at("algorithm").get<std::string>();
    ref.source_digest.value = resource.at("sourceDigest").at("value").get<std::string>();
    out.provenance.resources.push_back(std::move(ref));
  }

  out.contracts.reserve(plan.at("contracts").size());
  for (auto& contract : plan.at("contracts")) {
    Contract value;
    value.contract_id = contract.at("contractId").get<std::string>();
    value.schema_id = contract.at("schemaId").get<std::string>();
    value.schema_version = contract.at("schemaVersion").get<std::string>();
    out.contracts.push_back(std::move(value));
  }

  out.endpoints.reserve(plan.at("endpoints").size());
  for (auto& endpoint : plan.at("endpoints")) {
    Endpoint value;
    value.endpoint_id = endpoint.at("endpointId").get<std::string>();
    value.role = endpoint.at("role").get<std::string>();
    out.endpoints.push_back(std::move(value));
  }

  out.routes.reserve(plan.at("routes").size());
  for (auto& route : plan.at("routes")) {
    Route value;
    value.route_id = route.at("routeId").get<std::string>();
    value.from = route.at("from").get<std::string>();
    value.to = route.at("to").get<std::string>();
    value.contract_id = route.at("contractId").get<std::string>();
    out.routes.push_back(std::move(value));
  }

  out.providers.reserve(plan.at("providers").size());
  for (auto& provider : plan.at("providers")) {
    Provider value;
    value.provider_id = provider.at("providerId").get<std::string>();
    for (auto& capability : provider.at("capabilities")) {
      value.capabilities.push_back(capability.get<std::string>());
    }
    for (auto& required : provider.at("requiredCapabilities")) {
      value.required_capabilities.push_back(required.get<std::string>());
    }
    out.providers.push_back(std::move(value));
  }

  const json& policies = plan.at("policies");
  out.policies.ordering = policies.at("ordering").get<std::string>();
  out.policies.reliability = policies.at("reliability").get<std::string>();
  out.policies.overflow = policies.at("overflow").get<std::string>();
  out.policies.backpressure = policies.at("backpressure").get<std::string>();
  out.policies.deadline_ms = json_integer(policies.at("deadlineMs"));
  out.policies.retry = json_integer(policies.at("retry"));
  out.policies.queue_depth = json_integer(policies.at("queueDepth"));

  out.observation_points.reserve(plan.at("observationPoints").size());
  for (auto& tap : plan.at("observationPoints")) {
    ObservationPoint value;
    value.tap_id = tap.at("tapId").get<std::string>();
    value.route_id = tap.at("routeId").get<std::string>();
    value.payload_access = tap.at("payloadAccess").get<std::string>();
    value.validity_effect = tap.at("validityEffect").get<std::string>();
    out.observation_points.push_back(std::move(value));
  }

  for (auto& action : plan.at("stimulation").at("actions")) {
    out.stimulation.actions.push_back(action.get<std::string>());
  }
  for (auto& ref : plan.at("stimulation").at("permitPolicyRefs")) {
    out.stimulation.permit_policy_refs.push_back(ref.get<std::string>());
  }

  out.clock_domains.reserve(plan.at("clockDomains").size());
  for (auto& domain : plan.at("clockDomains")) {
    ClockDomain value;
    value.clock_domain_id = domain.at("clockDomainId").get<std::string>();
    value.source = domain.at("source").get<std::string>();
    out.clock_domains.push_back(std::move(value));
  }

  out.activation_order.reserve(plan.at("activationOrder").size());
  for (auto& entry : plan.at("activationOrder")) {
    out.activation_order.push_back(entry.get<std::string>());
  }

  out.diagnostics.reserve(plan.at("diagnostics").size());
  for (auto& diagnostic : plan.at("diagnostics")) {
    Diagnostic value;
    value.code = diagnostic.at("code").get<std::string>();
    value.severity = diagnostic.at("severity").get<std::string>();
    value.target_id = diagnostic.at("targetId").get<std::string>();
    out.diagnostics.push_back(std::move(value));
  }

  out.status = plan.at("status").get<std::string>();
  const json& resolution = plan.at("inputResolution");
  out.input_resolution.identity = resolution.at("identity").get<std::string>();
  out.input_resolution.schema = resolution.at("schema").get<std::string>();
  out.input_resolution.capability = resolution.at("capability").get<std::string>();
  out.input_resolution.time = resolution.at("time").get<std::string>();
  out.input_resolution.ownership = resolution.at("ownership").get<std::string>();
  out.input_resolution.policy = resolution.at("policy").get<std::string>();

  return true;
}

std::string domain_separator() {
  std::string separator(kPlanDomainSeparator);
  separator.push_back('\0');
  return separator;
}

}  // namespace

/// @brief True iff every `DecodeLimits` member is >= 1.
/// @param limits Bounded decode limits to validate.
/// @return `true` iff every member is >= 1.
bool is_valid(const DecodeLimits& limits) noexcept {
  return limits.max_bytes >= 1u && limits.max_depth >= 1u && limits.max_nodes >= 1u &&
         limits.max_string_length >= 1u && limits.max_contracts >= 1u &&
         limits.max_endpoints >= 1u && limits.max_routes >= 1u && limits.max_providers >= 1u &&
         limits.max_observation_points >= 1u && limits.max_clock_domains >= 1u &&
         limits.max_diagnostics >= 1u && limits.max_activation_order >= 1u &&
         limits.max_provenance_resources >= 1u;
}

/// @brief Lowercase-hex SHA-256 of the given bytes.
/// @param bytes Bytes to digest.
/// @return Lowercase-hex SHA-256 digest.
std::string sha256_hex(std::string_view bytes) {
  const std::array<std::uint8_t, 32> digest = sha256_bytes(bytes);
  static constexpr char kHex[] = "0123456789abcdef";
  std::string out;
  out.reserve(64);
  for (std::uint8_t byte : digest) {
    out.push_back(kHex[(byte >> 4u) & 0x0fu]);
    out.push_back(kHex[byte & 0x0fu]);
  }
  return out;
}

/// @brief Canonical bytes of the digested region (the plan value minus the top-level `digest`).
/// @param document_json Caller-supplied plan document bytes.
/// @param limits Bounded decode limits applied to the document.
/// @return Canonical digested-region bytes, or a rejected/failed result with an empty value.
BytesResult canonical_plan_body_bytes(std::string_view document_json, const DecodeLimits& limits) {
  json plan;
  DecodeError err;
  if (!parse_bounded(document_json, limits, plan, err)) {
    return bytes_from_error(err);
  }
  if (!validate_shape(plan, err)) {
    return bytes_from_error(err);
  }
  plan.erase("digest");
  BytesResult result;
  result.outcome = DecodeOutcome::accepted;
  if (!canonical_bytes(plan, result.value)) {
    return bytes_from_error(
        DecodeError{std::string(kCodeUnknown), std::string(kPlanTarget), "canonicalization defect"});
  }
  return result;
}

/// @brief Recomputed domain-separated SHA-256 hex of the plan body.
/// @param document_json Caller-supplied plan document bytes.
/// @param limits Bounded decode limits applied to the document.
/// @return Recomputed digest bytes, or a rejected/failed result with an empty value.
BytesResult recompute_plan_digest(std::string_view document_json, const DecodeLimits& limits) {
  const BytesResult body = canonical_plan_body_bytes(document_json, limits);
  if (body.outcome != DecodeOutcome::accepted) {
    return body;
  }
  BytesResult result;
  result.outcome = DecodeOutcome::accepted;
  result.value = sha256_hex(domain_separator() + body.value);
  return result;
}

/// @brief Bounded decode with independent version/digest/capability verification.
/// @param document_json Caller-supplied plan document bytes.
/// @param limits Bounded decode limits applied to the document.
/// @return The accepted decoded plan, or a rejected/failed result with a stable code and no plan.
DecodeResult decode_activation_plan(std::string_view document_json, const DecodeLimits& limits) {
  json plan;
  DecodeError err;
  if (!parse_bounded(document_json, limits, plan, err)) {
    return result_from_error(err);
  }
  if (!validate_shape(plan, err)) {
    return result_from_error(err);
  }

  if (plan.at("planVersion").get<std::string>() != kPlanVersion) {
    DecodeError version_error{std::string(kCodeVersion), std::string(kPlanTarget),
                              "planVersion must be exactly the declared version"};
    return result_from_error(version_error);
  }

  const json& recorded = plan.at("digest");
  if (recorded.at("algorithm").get<std::string>() != kDigestAlgorithm ||
      !is_hex64(recorded.at("value").get<std::string>())) {
    DecodeError digest_error{std::string(kCodeDigest), std::string(kPlanTarget),
                             "recorded digest form is invalid"};
    return result_from_error(digest_error);
  }

  const BytesResult body = canonical_plan_body_bytes(document_json, limits);
  if (body.outcome != DecodeOutcome::accepted) {
    return result_from_error(body.error);
  }
  const std::string recomputed = sha256_hex(domain_separator() + body.value);
  if (recomputed != recorded.at("value").get<std::string>()) {
    DecodeError digest_error{std::string(kCodeDigest), std::string(kPlanTarget),
                             "recorded digest does not match the recomputed digest"};
    return result_from_error(digest_error);
  }

  if (!validate_capability_and_references(plan, err)) {
    return result_from_error(err);
  }

  ActivationPlan model;
  if (!build_model(plan, limits, err, model)) {
    return result_from_error(err);
  }

  DecodeResult result;
  result.outcome = DecodeOutcome::accepted;
  result.plan = std::move(model);
  return result;
}

}  // namespace xverse::xcom::plan

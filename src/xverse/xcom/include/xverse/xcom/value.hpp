/**
 * @file value.hpp
 * @brief Fixed-capacity, value-owned primitives used by the X-COM core model.
 * @ownership Each value owns its text or bytes; no caller-owned view is retained.
 * @lifetime Returned views remain valid until the owning value is destroyed.
 * @thread_safety Independent values and concurrent const access are thread-safe.
 * @failure Factories reject invalid input without allocation, exceptions, or partial values.
 */

#ifndef XVERSE_XCOM_VALUE_HPP
#define XVERSE_XCOM_VALUE_HPP

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string_view>

namespace xverse::xcom {

/** Maximum UTF-8 byte count accepted for an identity. */
inline constexpr std::size_t kMaximumIdentityBytes = 128U;
/** Maximum UTF-8 byte count accepted for a semantic version. */
inline constexpr std::size_t kMaximumVersionBytes = 32U;
/** Maximum payload size retained by one core communication item. */
inline constexpr std::size_t kMaximumPayloadBytes = 65'536U;

namespace detail {

/**
 * @brief Internal fixed-capacity owned text storage.
 * @tparam Capacity Maximum retained byte count.
 * @ownership Owns its complete byte array and logical size.
 * @lifetime The view remains valid until the storage owner is destroyed.
 * @thread_safety Concurrent const reads are safe; mutation is private to construction.
 * @failure assign() returns false for over-capacity input and never allocates or throws.
 */
template <std::size_t Capacity>
class FixedText final {
 public:
  /** @brief Construct empty internal storage; this operation cannot fail. */
  constexpr FixedText() noexcept = default;

  /**
   * @brief Copy bounded bytes into owned storage.
   * @param text Bytes to retain.
   * @return true when the bytes fit; false without modification otherwise.
   */
  [[nodiscard]] constexpr bool assign(const std::string_view text) noexcept {
    if (text.size() > Capacity) {
      return false;
    }
    for (std::size_t index = 0U; index < text.size(); ++index) {
      bytes_[index] = text[index];
    }
    size_ = text.size();
    return true;
  }

  /** @return A view over the initialized owned bytes. */
  [[nodiscard]] constexpr std::string_view view() const noexcept {
    return {bytes_.data(), size_};
  }

  /** @return The initialized byte count. */
  [[nodiscard]] constexpr std::size_t size() const noexcept { return size_; }

  /**
   * @brief Compare initialized bytes and sizes.
   * @param left First storage value.
   * @param right Second storage value.
   * @return true when initialized content is equal.
   */
  friend constexpr bool operator==(const FixedText& left, const FixedText& right) = default;

 private:
  /** Owned zero-initialized byte capacity. */
  std::array<char, Capacity> bytes_{};
  /** Number of initialized bytes in bytes_. */
  std::size_t size_{0U};
};

}  // namespace detail

/**
 * @brief A non-empty bounded identity with value ownership.
 *
 * Identity validates only domain-neutral lexical safety and size. It does not
 * encode a provider, protocol, address, or physical realization.
 *
 * @ownership Owns fixed-capacity string storage.
 * @lifetime The value view remains valid until destruction. Construction from an
 * rvalue uses the copy constructor and leaves the source intact.
 * @thread_safety Concurrent const access is safe; instances expose no mutation.
 * @failure create() returns an empty optional for invalid input and is noexcept.
 */
class Identity final {
 public:
  /**
   * @brief Validate and copy one identity.
   * @param text Candidate identity encoded as bytes.
   * @return A validated value, or an empty optional on validation failure.
   */
  [[nodiscard]] static std::optional<Identity> create(std::string_view text) noexcept;

  /**
   * @brief Copy a validated identity without changing the source.
   * @param other Valid source identity.
   * @failure This operation cannot fail.
   */
  Identity(const Identity& other) noexcept = default;

  /** Assignment is disabled so previously returned views cannot be invalidated. */
  Identity& operator=(const Identity&) = delete;

  /** @return The immutable identity bytes. */
  [[nodiscard]] std::string_view value() const noexcept { return value_.view(); }

  /**
   * @brief Compare complete identity values.
   * @param left First identity.
   * @param right Second identity.
   * @return true when identity bytes are equal.
   */
  friend bool operator==(const Identity& left, const Identity& right) = default;

 private:
  /**
   * @brief Construct from already validated fixed storage.
   * @param value Owned validated bytes.
   * @failure This operation cannot fail.
   */
  explicit Identity(detail::FixedText<kMaximumIdentityBytes> value) noexcept : value_(value) {}

  /** Owned validated identity storage. */
  detail::FixedText<kMaximumIdentityBytes> value_;
};

/**
 * @brief A bounded semantic version in canonical major.minor.patch form.
 * @ownership Owns fixed-capacity string storage.
 * @lifetime The value view remains valid until destruction; rvalue construction copies.
 * @thread_safety Concurrent const access is safe; instances expose no mutation.
 * @failure create() returns an empty optional for malformed input and is noexcept.
 */
class SemanticVersion final {
 public:
  /**
   * @brief Validate and copy a semantic version.
   * @param text Candidate version.
   * @return A validated version, or an empty optional.
   */
  [[nodiscard]] static std::optional<SemanticVersion> create(std::string_view text) noexcept;

  /**
   * @brief Copy a validated version without changing the source.
   * @param other Valid source version.
   * @failure This operation cannot fail.
   */
  SemanticVersion(const SemanticVersion& other) noexcept = default;

  /** Assignment is disabled so previously returned views cannot be invalidated. */
  SemanticVersion& operator=(const SemanticVersion&) = delete;

  /** @return The immutable canonical version bytes. */
  [[nodiscard]] std::string_view value() const noexcept { return value_.view(); }

  /**
   * @brief Compare complete semantic-version values.
   * @param left First semantic version.
   * @param right Second semantic version.
   * @return true when canonical version bytes are equal.
   */
  friend bool operator==(const SemanticVersion& left, const SemanticVersion& right) = default;

 private:
  /**
   * @brief Construct from already validated fixed storage.
   * @param value Owned validated bytes.
   * @failure This operation cannot fail.
   */
  explicit SemanticVersion(detail::FixedText<kMaximumVersionBytes> value) noexcept : value_(value) {}

  /** Owned canonical version storage. */
  detail::FixedText<kMaximumVersionBytes> value_;
};

/**
 * @brief A bounded owned byte payload.
 * @ownership Copies bytes into fixed-capacity storage.
 * @lifetime The bytes view remains valid until destruction; rvalue construction copies.
 * @thread_safety Concurrent const reads are safe; no mutation is exposed.
 * @failure create() returns an empty optional when the explicit bound is exceeded.
 */
class Payload final {
 public:
  /**
   * @brief Copy a bounded payload.
   * @param bytes Payload bytes; empty payloads are valid.
   * @return A value-owned payload, or an empty optional when over-bound.
   */
  [[nodiscard]] static std::optional<Payload> create(std::span<const std::byte> bytes) noexcept;

  /**
   * @brief Copy a validated payload without changing the source.
   * @param other Valid source payload.
   * @failure This operation cannot fail.
   */
  Payload(const Payload& other) noexcept = default;

  /** Assignment is disabled so previously returned spans cannot be invalidated. */
  Payload& operator=(const Payload&) = delete;

  /** @return An immutable view of owned bytes. */
  [[nodiscard]] std::span<const std::byte> bytes() const noexcept {
    return {bytes_.data(), size_};
  }
  /** @return The number of owned bytes. */
  [[nodiscard]] std::size_t size() const noexcept { return size_; }

  /**
   * @brief Compare initialized payload bytes.
   * @param left First payload.
   * @param right Second payload.
   * @return true when size and initialized bytes are equal.
   */
  friend bool operator==(const Payload& left, const Payload& right) noexcept {
    return std::ranges::equal(left.bytes(), right.bytes());
  }

 private:
  /**
   * @brief Construct from bounded bytes already checked by create().
   * @param bytes Payload bytes within the declared bound.
   * @failure This operation cannot fail.
   */
  explicit Payload(std::span<const std::byte> bytes) noexcept;

  /** Owned fixed payload capacity. */
  std::array<std::byte, kMaximumPayloadBytes> bytes_{};
  /** Number of initialized payload bytes. */
  std::size_t size_{0U};
};

/**
 * @brief A signed timestamp paired with an explicit clock domain by CommunicationItem.
 * @ownership Stores the numeric value directly.
 * @lifetime Has ordinary value lifetime and no external references.
 * @thread_safety Concurrent reads are safe.
 * @failure Every signed nanosecond value is representable; cross-domain comparison is not provided.
 */
class Timestamp final {
 public:
  /**
   * @brief Construct an explicit nanosecond value.
   * @param nanoseconds Signed timestamp magnitude.
   * @failure This operation cannot fail.
   */
  explicit constexpr Timestamp(std::int64_t nanoseconds) noexcept : nanoseconds_(nanoseconds) {}

  /** @return The signed nanosecond value without a clock-domain inference. */
  [[nodiscard]] constexpr std::int64_t nanoseconds() const noexcept { return nanoseconds_; }

  /**
   * @brief Compare timestamp magnitudes without clock-domain inference.
   * @param left First timestamp.
   * @param right Second timestamp.
   * @return true when signed nanosecond magnitudes are equal.
   */
  friend bool operator==(const Timestamp& left, const Timestamp& right) = default;

 private:
  /** Signed nanosecond magnitude. */
  std::int64_t nanoseconds_;
};

}  // namespace xverse::xcom

#endif  // XVERSE_XCOM_VALUE_HPP

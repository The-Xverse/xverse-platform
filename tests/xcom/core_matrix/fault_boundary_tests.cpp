/**
 * @file fault_boundary_tests.cpp
 * @brief T016 XCOM-SW-CORE-008 / FR-024 controlled fault-hook boundary matrix.
 * @ownership The cases own no product resource; they inspect the committed public core headers and the
 * T016-owned public surface read-only.
 * @lifetime Per-case; no resource is retained beyond the case.
 * @thread_safety Single-threaded inspection.
 * @bounds A finite fixed list of committed headers, each read with a fixed size cap; no unbounded scan.
 * @failure A domain-specific fault primitive, an unbounded or ad-hoc injection entry point, or a
 * mutation path without an exact issued handle fails the case.
 */

#include "test_support.hpp"

#include <gtest/gtest.h>

#include <array>
#include <cctype>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>

namespace {

using namespace xverse::xcom;

/** Fixed, bounded list of committed T016-owned public core headers, in a stable order. */
constexpr std::array<std::string_view, 10U> kCoreHeaders{{
    "value.hpp",       "contract.hpp",     "item.hpp",      "diagnostic.hpp", "result.hpp",
    "core_types.hpp",  "endpoint_route_lifecycle.hpp",     "provider.hpp",   "loopback_provider.hpp",
    "observation.hpp",
}};

/** Fixed maximum committed-header bytes read for one scan. */
constexpr std::size_t kMaximumHeaderBytes = 262'144U;

/** @return true when the byte can appear inside a scanned vocabulary word. */
[[nodiscard]] bool is_word_char(const char character) noexcept {
  return (character >= 'a' && character <= 'z') || (character >= '0' && character <= '9') ||
         character == '_';
}

/** @return true when the lowercase haystack contains the needle at a word boundary. */
[[nodiscard]] bool contains_word(const std::string_view haystack,
                                 const std::string_view needle) noexcept {
  std::size_t position = haystack.find(needle);
  while (position != std::string_view::npos) {
    const bool left_ok = position == 0U || !is_word_char(haystack[position - 1U]);
    const std::size_t after = position + needle.size();
    const bool right_ok = after >= haystack.size() || !is_word_char(haystack[after]);
    if (left_ok && right_ok) {
      return true;
    }
    position = haystack.find(needle, position + 1U);
  }
  return false;
}

/** @return the lowercase committed-header content, or an empty string when it cannot be read. */
[[nodiscard]] std::string read_lowercase_header(const std::string_view name) {
  const std::string path = std::string(XCOM_T016_INCLUDE_DIR) + "/" + std::string(name);
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    return {};
  }
  std::string content;
  content.resize(kMaximumHeaderBytes);
  stream.read(content.data(), static_cast<std::streamsize>(content.size()));
  content.resize(static_cast<std::size_t>(stream.gcount()));
  for (char& character : content) {
    character = static_cast<char>(std::tolower(static_cast<unsigned char>(character)));
  }
  return content;
}

/** Detects a composition operation that would accept a raw provider-route token instead of a handle. */
template <typename T, typename = void>
struct accepts_raw_token : std::false_type {};
template <typename T>
struct accepts_raw_token<
    T, std::void_t<decltype(std::declval<T&>().submit(
           std::declval<const ProviderRouteToken&>(), std::declval<const CommunicationItem&>(),
           std::declval<const LifecycleController&>()))>> : std::true_type {};

/** Detects a composition state query that would accept a raw provider-route token. */
template <typename T, typename = void>
struct accepts_raw_token_state : std::false_type {};
template <typename T>
struct accepts_raw_token_state<T, std::void_t<decltype(std::declval<const T&>().route_state(
                                          std::declval<const ProviderRouteToken&>()))>>
    : std::true_type {};

}  // namespace

/** CHK-17: no committed public core header embeds a domain-specific fault vocabulary. */
TEST(CoreMatrixFaultBoundary, CoreSurface_ExposesNoDomainSpecificFaultSemantics) {
  constexpr std::array<std::string_view, 8U> forbidden{{
      "fault", "inject", "campaign", "taxonomy", "fuzz", "vehicle", "autosar", "cruise",
  }};
  for (const std::string_view name : kCoreHeaders) {
    const std::string content = read_lowercase_header(name);
    ASSERT_FALSE(content.empty()) << "committed core header is unreadable: " << name;
    for (const std::string_view token : forbidden) {
      EXPECT_FALSE(contains_word(content, token))
          << "forbidden domain/fault vocabulary '" << token << "' in " << name;
    }
  }
}

/** CHK-17: the only extension seams are the bounded, controlled provider and observation seams. */
TEST(CoreMatrixFaultBoundary, CoreSurface_ExposesOnlyBoundedControlledSeams) {
  static_assert(std::is_abstract_v<CommunicationProvider>,
                "the provider seam must remain an abstract source-level interface");
  static_assert(!std::is_copy_constructible_v<ProviderComposition>,
                "the registry must not be copyable");
  static_assert(!std::is_copy_constructible_v<ObservationHub>,
                "the observation hub must not be copyable");
  static_assert(!std::is_copy_constructible_v<LifecycleController>,
                "the lifecycle controller must not be copyable");
  static_assert(!std::is_move_constructible_v<LifecycleController>,
                "the lifecycle controller must not be movable");
  EXPECT_TRUE(std::is_abstract_v<CommunicationProvider>);
  // A configuration-only lifecycle controller exposes no unbounded capacity.
  EXPECT_EQ(LifecycleController::kMaximumEndpoints, 32U);
  EXPECT_EQ(LifecycleController::kMaximumRoutes, 32U);
  EXPECT_EQ(ProviderComposition::kMaximumProviders, 8U);
}

/** CHK-17: no public operation mutates a route, queue, or record without an exact issued handle. */
TEST(CoreMatrixFaultBoundary, CoreSurface_HasNoUncontrolledMutationEntryPoint) {
  static_assert(!accepts_raw_token<ProviderComposition>::value,
                "submit must require an exact ProviderRouteHandle");
  static_assert(!accepts_raw_token_state<ProviderComposition>::value,
                "route_state must require an exact ProviderRouteHandle");
  EXPECT_FALSE(accepts_raw_token<ProviderComposition>::value);
  EXPECT_FALSE(accepts_raw_token_state<ProviderComposition>::value);
  // A healthy stack proves the exact-handle path is the only one that succeeds.
  xverse::xcom::test::CoreStackFixture fixture(InteractionKind::message_event, "fault.boundary", 1U,
                                               16U, true);
  ASSERT_TRUE(fixture.ready());
  ASSERT_TRUE(fixture.activated());
  EXPECT_TRUE(fixture.route_state().has_value());
}

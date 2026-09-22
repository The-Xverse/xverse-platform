/**
 * @file provider_mutation_rejection.cpp
 * @brief Deliberately uncompilable external-consumer provider mutation probes.
 * @ownership The declarations retain no resource and own no provider state.
 * @lifetime All references are call-scoped and are never retained.
 * @thread_safety No probe may compile, so no shared mutation can execute.
 * @failure Each selected probe must fail access checking for its selected provider type.
 */

#include "xverse/xcom/loopback_provider.hpp"

namespace xverse::xcom::external_consumer_probe {

/** Select one raw mutation call that must be inaccessible to an external consumer. */
void invoke_raw_mutation(
    CommunicationProvider& interface_provider, LoopbackProvider& concrete_provider,
    const ProviderRouteBinding& binding, const ProviderRouteToken& token,
    const CommunicationItem& item, const LifecycleController& lifecycle) {
#if defined(XCOM_PROBE_CONTROL)
  static_cast<void>(interface_provider.descriptor());
  static_cast<void>(concrete_provider.descriptor());
  static_cast<void>(binding);
  static_cast<void>(token);
  static_cast<void>(item);
  static_cast<void>(lifecycle);
#elif defined(XCOM_PROBE_PREPARE)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.prepare(binding));
#else
  static_cast<void>(interface_provider.prepare(binding));
#endif
#elif defined(XCOM_PROBE_ACTIVATE)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.activate(token, lifecycle));
#else
  static_cast<void>(interface_provider.activate(token, lifecycle));
#endif
#elif defined(XCOM_PROBE_SUBMIT)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.submit(token, item, lifecycle));
#else
  static_cast<void>(interface_provider.submit(token, item, lifecycle));
#endif
#elif defined(XCOM_PROBE_RECEIVE)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.receive(token, lifecycle));
#else
  static_cast<void>(interface_provider.receive(token, lifecycle));
#endif
#elif defined(XCOM_PROBE_DRAIN)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.drain(token, lifecycle));
#else
  static_cast<void>(interface_provider.drain(token, lifecycle));
#endif
#elif defined(XCOM_PROBE_CLOSE)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.close(token, lifecycle));
#else
  static_cast<void>(interface_provider.close(token, lifecycle));
#endif
#elif defined(XCOM_PROBE_STATE)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.state(token));
#else
  static_cast<void>(interface_provider.state(token));
#endif
#elif defined(XCOM_PROBE_RECONCILE)
#if defined(XCOM_PROBE_CONCRETE)
  static_cast<void>(concrete_provider.reconcile(token, lifecycle));
#else
  static_cast<void>(interface_provider.reconcile(token, lifecycle));
#endif
#else
#error "select exactly one XCOM provider mutation rejection probe"
#endif
}

}  // namespace xverse::xcom::external_consumer_probe

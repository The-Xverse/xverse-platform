/**
 * @file core_types.hpp
 * @brief Convenience include for the bounded X-COM core value model.
 * @ownership Included types are value-owned and retain no caller storage.
 * @lifetime Included accessor views follow their owning value lifetime.
 * @thread_safety Included values support concurrent const access.
 * @failure Included factories report bounded validation failures explicitly.
 */

#ifndef XVERSE_XCOM_CORE_TYPES_HPP
#define XVERSE_XCOM_CORE_TYPES_HPP

#include "xverse/xcom/contract.hpp"
#include "xverse/xcom/diagnostic.hpp"
#include "xverse/xcom/item.hpp"
#include "xverse/xcom/result.hpp"
#include "xverse/xcom/value.hpp"

#endif  // XVERSE_XCOM_CORE_TYPES_HPP

#!/usr/bin/env bash
# Tear down the CDE test fixture. Safe to re-run (ignores missing objects).
# Deletes only the namespaces this fixture created; the StorageClass is cluster
# scoped so it is removed explicitly.
set -euo pipefail

echo "Deleting CDE fixture namespaces (payments, sandbox)..."
kubectl delete namespace payments sandbox --ignore-not-found=true

echo "Deleting cluster-scoped StorageClass..."
kubectl delete storageclass payments-encrypted --ignore-not-found=true

echo "Teardown complete. Verify with: kubectl get ns"

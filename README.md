# secure-ml-supply-chain-lab

A small lab that proves one idea end to end: **the cluster only runs images
that my release pipeline built, scanned and signed.**

The app is a stub inference API. The interesting part is the path from a
commit to a running pod.

## What the pipeline does, and why

| Step | Tool | Why it exists |
|---|---|---|
| Actions pinned to commit hashes | GitHub Actions | A tag like `v4` can be repointed at malicious code. A commit hash cannot. |
| Zero default permissions | `permissions: {}` | The job token can only do what the job needs. |
| Build and push by digest | Buildx, GHCR | A digest identifies exact bytes. A tag is only a label. |
| Vulnerability scan as a gate | Grype | A failed scan stops the job before signing, so the image can never be deployed. |
| SBOM | Syft (CycloneDX) | A list of everything inside the image, so a new CVE can be matched to it later. |
| Keyless signing | cosign, GitHub OIDC | No long-lived signing key to steal. The signature is bound to this workflow's identity. |
| Signed SBOM attestation | cosign attest | The SBOM is tied to the image and cannot be swapped. |
| Build provenance | GitHub attestations (SLSA) | A signed record of which repo, commit and workflow produced the image. |
| Admission control | Kyverno on GKE | The cluster checks the signature and SBOM itself and rejects anything else. |

## Run it

1. Create a public GitHub repo named `secure-ml-supply-chain-lab` and push these files to `main`.
2. Wait for the `release` workflow to pass. Copy the image digest from the run summary.
3. Make the GHCR package public (Package settings, Change visibility) so the cluster can pull it.
4. Verify the signature from your laptop:

   ```sh
   cosign verify ghcr.io/prameetkulkarni/secure-ml-supply-chain-lab@sha256:DIGEST \
     --certificate-identity "https://github.com/prameetkulkarni/secure-ml-supply-chain-lab/.github/workflows/release.yml@refs/heads/main" \
     --certificate-oidc-issuer https://token.actions.githubusercontent.com
   ```

5. Create a small GKE Standard cluster and install Kyverno:

   ```sh
   helm repo add kyverno https://kyverno.github.io/kyverno/
   helm install kyverno kyverno/kyverno -n kyverno --create-namespace
   ```

6. Put the digest into `k8s/deploy-signed.yaml`, then:

   ```sh
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/policy-require-signed.yaml
   kubectl apply -f k8s/deploy-unsigned.yaml   # must be REJECTED
   kubectl apply -f k8s/deploy-signed.yaml     # must be ADMITTED
   kubectl -n demo get pods
   ```

7. Screenshot the rejection message and the running pod and add both to this README. That is the evidence.
8. Delete the cluster when you are done so it stops costing money.

## If it does not work first time

- **Unsigned pod is admitted:** the policy is not matching. Check `kubectl get imagevalidatingpolicy` and the namespace label.
- **Signed pod is rejected with "no signatures found":** cosign and Kyverno may disagree on the signature storage format. Compare the cosign version in the workflow log with the formats your Kyverno version supports.
- **Identity mismatch:** the `subject` in the policy must equal the certificate identity exactly, including case and the branch ref.

## Stretch goals (the AI part)

1. **Treat the model as an artefact.** Add a small model file in `safetensors` format, sign it with `cosign sign-blob` in the pipeline, and make the app verify it before loading. Explain why pickle-format models are a code-execution risk.
2. **Scan the model** with a model scanner in the pipeline and fail the build on unsafe operators.
3. **Short-lived cloud credentials.** Push to Google Artifact Registry using Workload Identity Federation instead of a stored service-account key.
4. **Compare with GKE Binary Authorization**, the native alternative to Kyverno, and write down the trade-offs.
5. **Write a STRIDE threat model** of the pipeline in `THREAT_MODEL.md`: what does each control stop, and what still gets through (for example, a malicious commit merged to main is signed like any other).

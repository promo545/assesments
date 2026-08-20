# Test Plan: Reliable Document Processing Service

This document outlines the testing strategy for the document processing component. The scenarios are designed to validate business rules, ensure fault tolerance, and verify dependency interactions.

## 1. Happy Paths
*   Submit a valid document successfully, ensuring ID generation and storage upload occur.
*   Process a clean document, verifying the status transitions to `PROCESSED`.

## 2. Invalid Inputs
*   Attempt submission with an empty filename.
*   Attempt submission with a whitespace-only filename.
*   Attempt submission with an unsupported extension (e.g., `.exe`).
*   Attempt submission with empty or whitespace-only file content.
*   Attempt submission with a filename exceeding 255 characters.

## 3. Boundary Cases
*   Submit a document with an upper-case valid extension (e.g., `.PDF`) to verify case-insensitivity.
*   Submit a document with a filename of exactly 255 characters.

## 4. Idempotency Cases
*   Reject duplicate submission if the existing document is `PENDING`.
*   Reject duplicate submission if the existing document is `SCANNING`.
*   Reject duplicate submission if the existing document is `PROCESSED`.
*   Allow duplicate submission if the existing document is `FAILED`.
*   Allow duplicate submission if the existing document is `REJECTED`.

## 5. Dependency Failures
*   Repository save fails during submission (must trigger storage cleanup).
*   Scanner is immediately unavailable (raises `ScannerUnavailable` and marks document as `FAILED`).
*   File content is missing from storage during processing (raises `FileContentNotFoundError`).

## 6. State-Transition Cases
*   Attempt to process a document that is already `PROCESSED` (must raise `DocumentAlreadyProcessed`).
*   Process an infected document, ensuring the file is deleted from storage and status becomes `REJECTED`.

## 7. Retry Cases
*   Scanner times out once, then succeeds on the second attempt.
*   Scanner times out twice, then succeeds on the third attempt.
*   Scanner times out three consecutive times, resulting in a `FAILED` status.

## 8. Unexpected Failures (The "Nasty Production Failure")
*   Repository save fails, triggering storage cleanup, but the storage cleanup (`delete`) also fails.

## 9. Blocked Owner Policy
*   Reject submission immediately if the owner ID is on the blocked list.
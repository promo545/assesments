# Reliable Document Processing Service

A resilient backend service layer responsible for coordinating document ingestion, metadata tracking, and malware scanning[cite: 25]. This project demonstrates robust dependency management, fault tolerance, and test-driven development methodologies[cite: 25].

## Development Workflow: Organic TDD

The development process strictly adhered to a Red-Green-Refactor cycle[cite: 25]. To genuinely drive the design through tests, I employed the following workflow:
1.  **Red:** Authored a failing test outlining the expected behavior[cite: 25]. In the business logic layer, I initially placed `NotImplementedError` or `...` stubs[cite: 25].
2.  **Green:** Implemented the minimal functional code required to make the test pass[cite: 25]. 
3.  **Refactor:** Refined the code architecture, evolving method signatures and extracting Pytest fixtures organically as test complexity grew[cite: 25].

## Architectural & Design Decisions

### Part 7: The "Nasty Production Failure"
**Scenario:** `storage.upload()` succeeds, `repository.save()` fails, and the subsequent fallback `storage.delete()` also fails[cite: 25].

**Decision:** When metadata persistence fails, the system must not leave orphaned files in storage[cite: 25]. The service attempts to clean up the uploaded object[cite: 25]. If the `delete` operation also fails, I opted to let the secondary storage exception propagate[cite: 25]. Propagating the error ensures the failure is completely observable and does not silently swallow the infrastructure malfunction[cite: 25]. The test suite explicitly proves that the upload is attempted, the save failure triggers the deletion sequence, and the system halts correctly without masking the broken state[cite: 25].

### Part 10: Mock-Based Behavioral Verification
**Scenario:** Testing complex flows like retries and failures without polluting production code.

**Decision:** The project utilizes `unittest.mock.Mock` bound to interface protocols (`Port` abstractions). This enables precise tracking of interactions (such as `call_count` and `side_effect` configurations) without requiring bespoke in-memory fakes inside the source directory, keeping core domain code entirely clean and focused strictly on business rules.

## Running the Tests Coverage

Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/document_processing/exceptions.py      18      0   100%[cite: 26]
src/document_processing/models.py          40      2    95%   41, 50[cite: 26]
src/document_processing/ports.py           42      1    98%   70[cite: 26]
src/document_processing/processor.py        84      0   100%
---------------------------------------------------------------------
TOTAL                                     184      3    98%
# Reliable Document Processing Service

A resilient backend service layer responsible for coordinating document ingestion, metadata tracking, and malware scanning. This project demonstrates robust dependency management, fault tolerance, and test-driven development methodologies.

## Development Workflow: Organic TDD

The development process strictly adhered to a Red-Green-Refactor cycle. To genuinely drive the design through tests, I employed the following workflow:
1.  **Red:** Authored a failing test outlining the expected behavior. In the business logic layer, I initially placed `NotImplementedError` or `...` stubs.
2.  **Green:** Implemented the minimal functional code required to make the test pass. 
3.  **Refactor:** Refined the code architecture, evolving method signatures and extracting Pytest fixtures organically as test complexity grew.

## Architectural & Design Decisions

### Part 7: The "Nasty Production Failure"
**Scenario:** `storage.upload()` succeeds, `repository.save()` fails, and the subsequent fallback `storage.delete()` also fails.

**Decision:** When metadata persistence fails, the system must not leave orphaned files in storage. The service attempts to clean up the uploaded object. If the `delete` operation also fails, the system intentionally swallows this secondary storage exception and propagates the original repository error. This ensures the root cause of the failure remains completely observable and is not masked by subsequent infrastructure hiccups during the cleanup phase.

### Part 10: Mock-Based Behavioral Verification
**Scenario:** Testing complex flows like retries and failures without polluting production code.

**Decision:** The project utilizes `unittest.mock.Mock` bound to interface protocols (`Port` abstractions). This enables precise tracking of interactions (such as `call_count` and `side_effect` configurations) without requiring bespoke in-memory fakes inside the source directory, keeping core domain code entirely clean and focused strictly on business rules.

## Running the Tests Coverage

Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/document_processing/exceptions.py      18      0   100%
src/document_processing/models.py          40      2    95%   41, 50
src/document_processing/ports.py           42      1    98%   70
src/document_processing/processor.py        84      0   100%
---------------------------------------------------------------------
TOTAL                                     184      3    98%
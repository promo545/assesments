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

**Decision:** When metadata persistence fails, the system must not leave orphaned files in storage. The service attempts to clean up the uploaded object. If the `delete` operation also fails, I opted to let the secondary storage exception propagate. Propagating the error ensures the failure is completely observable and does not silently swallow the infrastructure malfunction. The test suite explicitly proves that the upload is attempted, the save failure triggers the deletion sequence, and the system halts correctly without masking the broken state.

### Part 16: Debugging Challenge Answer
**Scenario:** A retry test expected 3 scanner calls but reported `Actual: 1`.
**Question:** Where is the bug?

**Answer:** The bug is in the **production implementation**. 

**How I determined this:**
If the framework reports an `AssertionError` stating `Expected: 3, Actual: 1`, it guarantees that the test execution successfully reached the `assert scanner.scan.call_count == 3` line. 
* If the bug were in the **test** (e.g., a missing `pytest.raises(ScannerTimeout)` block), the unhandled exception would have crashed the test during `processor.process(...)`, resulting in an Exception traceback, *not* an assertion failure. 
* If the bug were in the **mock** or **fixture** (e.g., the processor was injected with a different mock instance than the one being asserted), the actual call count would be `0`. 
* Therefore, the `processor` executed, caught the `ScannerTimeout` on the first attempt, swallowed the error, and successfully returned *without looping*. The implementation failed to retry.

## Running the Tests Coverage

Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/document_processing/exceptions.py      18      0   100%
src/document_processing/models.py          40      2    95%   41, 50
src/document_processing/ports.py           42      1    98%   70
src/document_processing/processor.py        84      5    94%   30, 34-37
---------------------------------------------------------------------
TOTAL                                     184      8    96%
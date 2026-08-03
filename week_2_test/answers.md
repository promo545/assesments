# Section A 

# Theory

1 : In the dependency inverison principal the class/method which requiures the object must not be the one who must manage the life cycle of the object instead all it must assume is it'll recive the object prehand and only think of buisness logic; not the life cycle.
The high level service must be able to extend itslef to perform same logic across different objects so it's better to abstract the implementaion and use the inversion principal to decouple the responsibilites

2 : Inheritance tightly couples classes through a rigid structural hierarchy , whereas composition promotes loose coupling by assembling independent objects via public interfaces

Composition is the superior choice for injecting orthogonal, dynamic behaviors—such as passing an interchangeable retry strategy into a processing service—without locking it into a fixed hierarchy. Conversely, inheritance is specifically justified when establishing strict type taxonomies, such as defining custom exception hierarchies where the language runtime relies on base classes for polymorphic error handling.

3 : Strategy pattern is to decide what must be done based on the situation, say some request must use email channel some other different and this cwitching of logic happens at run time.
it solves the problem of chooosing the right desicions according to situation

    Factory pattern is to decide what to create, its simple a service requests the object a particular class is reponsible to supply the objects to the requesting service.
    it solve the decoupling of managing the life cycle of object from the buisness service

4 : abstract class helps in making polymorphism easy to implement where any sub class inheriting the base calss must define the methods in its own leading to less runtime errors
protocal it allows to duck type making to work with external code easily instead of modifying the external code to forcefully inherit from the class we define all we care is if the class has that method and just execute.

5 - Temperory failures are not critical as they do not modify the business logic and can be retried with possibilty of having a success whereas the invalid user input is something critical to the buisness logic its important to handle and fail immediatly and even if we try again its bound that it'll fail and thiers a possibilty that we overide the original erro with the latest when retrying masking critical information

# Section B

present in src folder

# Section C
present in the tests folder

# Section D
issue 1 : missing return in try block, which will cause an the operation to be executed again and again until the attempts are exhausted 
issue 2 : catching Exception is very broad which can cause anomalies in the service layer and the transperency to upper layers
issue 3 : the loop is short by 1, it must be max_attempt + 1
issue 4 : sleep must be after the check of max attempts leaving the app waste time
issue 5 : rasing e is not correct as it'll maske the first error which was caught and will give the latest error which was caught

debug : checking phone_number wheras the logic is used for checking the device_token

# Section D
# Part A
Here is a structured textual design outlining the notification system's architecture.

* **Major Classes and Abstractions**
* **`Processor`**: The core orchestrator managing the delivery workflow.


* **`Base`**: An abstraction representing a generic notification channel.


* **`RetryStrategy`**: An interface defining the execution protocol for delivery attempts.


* **`NotificationRepository`**: The central data access layer handling storage operations.


* **`NotificationFactory`**: The instantiation engine for concrete channels.


* **Models**: `NotificationRequest` (input payload) and `DeliveryRecord` (system representation).




* **Dependency Direction**
* The `Processor` relies downwards on `RetryStrategy`, `NotificationFactory`, and `NotificationRepository` to execute its tasks.


* `NotificationFactory` depends on the `Base` interface and its concrete implementations (`EmailChannel`, `PushChannel`, `SMSChannel`).


* Concrete channels depend on the `NotificationRepository` to fetch required state.




* **Composition Relationships**
* The `Processor` is composed with a `RetryStrategy` at initialization.


* The `NotificationRepository` encapsulates a collection of `DeliveryRecord` instances.


* Each `DeliveryRecord` encapsulates a `NotificationRequest` and a `NotificationStatus`.




* **State Ownership**
* State is strictly owned and managed by the `NotificationRepository`. It utilizes an internal dictionary to hold `DeliveryRecord`s and governs status transitions.




* **Extension Points**
* New channel types can be introduced by subclassing `Base` and mapping them in `NotificationFactory`.


* New execution logic can be introduced by creating new classes implementing the `RetryStrategy` interface.




* **Design Pattern Implementations**
* **Strategy**: Appears via `RetryStrategy`. It is injected into the `Processor` constructor, allowing the retry behavior (such as `FixedRetry`) to vary independently of the processor logic.


* **Factory**: Appears via `NotificationFactory`. It delegates the creation of specific channel objects during the `Processor`'s execution phase, abstracting away the instantiation details.





---

### Adding ExponentialBackoffRetryStrategy

To implement an `ExponentialBackoffRetryStrategy` without altering the `Processor`, you leverage the existing dependency injection framework.

Because the `Processor` is designed to accept any object adhering to the `RetryStrategy` abstraction during instantiation, you only need to create a new class named `ExponentialBackoffRetryStrategy` that inherits from `RetryStrategy`. This new class must implement the `execute(self, operation: Callable)` method with your backoff logic. You can then instantiate the processor natively by passing the new strategy directly: `Processor(ExponentialBackoffRetryStrategy(...))`. The `Processor` will execute the new logic seamlessly.

# Part B
API Layer: Serves as the gateway for ingesting client requests and querying delivery statuses. It enforces authentication, rate limiting, and preliminary payload validation.

Queue or Background Worker: Decouples ingestion from execution by asynchronously buffering tasks. This ensures the API remains highly responsive while background workers handle time-consuming processes like retries and backoffs.

Notification Service: The core orchestration engine that consumes jobs from the queue. It applies your configured delivery strategies and routes the payload to the correct communication channel.

Durable Database: Replaces the volatile in-memory repository with persistent storage, such as PostgreSQL or MongoDB. It safeguards delivery records, audit trails, and state transitions against system crashes.

External Providers: Third-party vendor integrations (like AWS SES for email, Twilio for SMS, or FCM for push) that facilitate the actual transmission of messages to the end user.

Logging and Monitoring: Captures comprehensive system telemetry, error traces, and performance metrics. This provides visibility into delivery success rates and triggers alerts during operational anomalies.

# Section F

1 : def first_unique_event(event_ids: list[int]) -> int | None:
    if not event_ids:
        return None
        
    frequencies = {}
    for event_id in event_ids:
        frequencies[event_id] = frequencies.get(event_id, 0) + 1
        
    for event_id in event_ids:
        if frequencies[event_id] == 1:
            return event_id
            
    return None

# --- Tests ---
def test_first_unique_event():
    assert first_unique_event([4, 5, 1, 2, 1, 4, 2]) == 5
    assert first_unique_event([]) is None  # Empty list
    assert first_unique_event([1, 1, 2, 2]) is None  # No unique events
    assert first_unique_event([7]) == 7  # Single element
    print("All Q1 tests passed.")

2 : def merge_delivery_windows(windows: list[list[int]]) -> list[list[int]]:
    if not windows:
        return []

    # Helper function replacing the lambda
    def get_start_time(window: list[int]) -> int:
        return window[0]

    windows.sort(key=get_start_time)
    merged = [windows[0]]

    for current in windows[1:]:
        last_merged = merged[-1]
        
        if current[0] <= last_merged[1]:
            last_merged[1] = max(last_merged[1], current[1])
        else:
            merged.append(current)

    return merged

# Section G

1 : not having the channel type injected in the processor made it hard to test with mock channel as i had only few suported types, i though of putting full logic inside a single method but that was too complex and crumbly  so instead i went with making a mock factory and used that.

2 : DI made it simple to just create different objects and just pass as param to testing instead of making a object for each test, mainly the pytest fixtures simple take the fresh objects and have clean env

3 : imports were messy so i searched for having the mypy.ini at root and use absolute path of modules, se of __int__.py for packages, using kwargs, retry test where the logic was not reaching the path where it updates the status to failed so the tests were failing with pending ! failed. because i used invalid request which is not caught by retry so the send would raise the exception and the test will not catch and crash which is expected

4 : Dynamic Factory: Remove the hardcoded map in the NotificationFactory. Instead, allow channels to register themselves dynamically to keep the codebase clean and extensible. 
 Generic Payloads: Stop adding channel-specific fields (like device_token or phone_number) to the NotificationRequest. Use a flexible dictionary to hold these diverse details.  
5 : mainly in factory.py where we create particular objects when requested, tried to keep implemenation clean by using map instead of if else making it extendable to some extent but not for large number channle i think i use the srp for factory and processor, retry which have clear responsibilty of having single operation only thing is i am making the deliveryrecord in processor but it was mentioed in the test to do that, and the o principle for keeping open and extensable its the dict usage


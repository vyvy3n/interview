---
layout: ../../layouts/Layout.astro
title: OOD Principles
---

# OOD Principles

> Object-Oriented Design interviews test how you turn fuzzy requirements into a class diagram with right responsibilities, relationships, and access controls.

## The 3 pillars

| Pillar | One-line | Watch for |
|---|---|---|
| **封装 Encapsulation** | hide state, expose behavior via methods | use `private` fields + getter/setter or domain methods |
| **继承 Inheritance** | child classes reuse parent's structure | "is-a" relationships only |
| **多态 Polymorphism** | one interface, many implementations | overriding + overloading; Strategy / Factory patterns |

## SOLID

| | Principle | What it forbids |
|---|---|---|
| **S** | Single Responsibility | one class doing 5 unrelated jobs |
| **O** | Open / Closed | modifying an existing class to add new behavior (extend instead) |
| **L** | Liskov Substitution | subclass that breaks parent's contract (e.g. `Square extends Rectangle` then `setWidth` breaks `setHeight`) |
| **I** | Interface Segregation | fat interfaces forcing classes to stub methods they don't use |
| **D** | Dependency Inversion | depending on a concrete class instead of an abstraction |

> Liskov example: if every `Bird` has `fly()`, `Penguin extends Bird` violates LSP. Better: factor `Flyable` interface, `Penguin extends Bird implements Swimmable`.

## The 5 C's — interview procedure

Use this every time the prompt is "design X":

| Step | What to do |
|---|---|
| **1. Clarify** | Pin down ambiguous scope — "do we support multi-floor parking lots? motorcycles?" Confirm input/output. |
| **2. Core Objects** | Identify the few real-world *nouns* — `Car`, `Spot`, `Lot`. List their relationships (1:1, 1:N, M:N). |
| **3. Cases (use cases)** | Turn requirements into verbs — `parkCar`, `unpark`, `lotIsFull`. These become methods. |
| **4. Classes** | Draw the class diagram: fields, methods, access modifiers, relations. Pick the right design patterns. |
| **5. Correctness** | Walk through edge cases — full lot? invalid ticket? concurrent parks? |

## Abstract class vs interface — when which

```
Abstract class:                    Interface:
- has fields + methods             - method signatures only (Java <8)
- single inheritance               - multiple inheritance
- "is a kind of"                   - "can do this thing"
- shared implementation            - contract / capability
```

In Python: abstract base classes via `abc.ABC`; in Java: `abstract class` vs `interface` (with default methods since 8).

## Common patterns to recognize and use

| Pattern | When |
|---|---|
| **Singleton** | exactly one instance (config, lot manager, cache) |
| **Factory** | hide which concrete subclass to construct |
| **Strategy** | interchangeable algorithms (payment, sort, pricing) |
| **Observer** | event subscribers (UI, pub-sub) |
| **State** | object behaves differently per state (parking gate states) |
| **Decorator** | dynamically add behavior (food toppings, logging) |
| **Adapter** | bridge an old API to a new interface |
| **Builder** | construct a complex object step-by-step (request, query) |

### Singleton — thread-safe Java pattern

```java
public class ParkingLot {
    private ParkingLot() {}                   // block external `new`
    private static class Holder {             // class-load = thread-safe lazy init
        static final ParkingLot INSTANCE = new ParkingLot();
    }
    public static ParkingLot getInstance() {
        return Holder.INSTANCE;
    }
}
```

The static-inner-holder idiom defers init until first `getInstance()` and is automatically thread-safe via class-loading guarantees — no `synchronized` needed.

## UML access modifiers — what the symbols mean

![](/notes/ood/media/image3.png)

| Symbol | Visibility |
|---|---|
| `+` | public — anywhere |
| `-` | private — only this class |
| `#` | protected — this class + subclasses |
| (none) | package-private (default in same package) |

## Worked example: Parking Lot

**1. Clarify** — Multiple floors? Multiple spot sizes (compact / regular / motorcycle)? Reservation in advance? Pricing?

**2. Core objects** — `Vehicle`, `ParkingSpot`, `Floor`, `ParkingLot`, `Ticket`. Relationships: `ParkingLot` 1↔N `Floor`; `Floor` 1↔N `ParkingSpot`; `ParkingSpot` 1↔0..1 `Vehicle`.

**3. Cases** — `parkVehicle(v) → Ticket`, `unparkVehicle(t) → fee`, `findAvailableSpot(size)`, `isLotFull()`.

**4. Classes**

```python
from enum import Enum
from abc import ABC, abstractmethod

class VehicleSize(Enum):
    MOTORCYCLE = 1
    COMPACT    = 2
    LARGE      = 3

class Vehicle(ABC):
    def __init__(self, plate, size):
        self.plate, self.size = plate, size

class Motorcycle(Vehicle):
    def __init__(self, plate): super().__init__(plate, VehicleSize.MOTORCYCLE)

class Car(Vehicle):
    def __init__(self, plate): super().__init__(plate, VehicleSize.COMPACT)

class ParkingSpot:
    def __init__(self, spot_id, size):
        self.id, self.size = spot_id, size
        self.vehicle = None
    def fits(self, v): return v.size.value <= self.size.value
    def park(self, v): self.vehicle = v
    def vacate(self):  v, self.vehicle = self.vehicle, None; return v

class Ticket:
    def __init__(self, vehicle, spot, ts):
        self.vehicle, self.spot, self.ts = vehicle, spot, ts

class ParkingLot:                              # singleton
    _instance = None
    def __new__(cls, floors):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.floors = floors
        return cls._instance
    def park(self, v):
        for f in self.floors:
            spot = f.find_spot(v)
            if spot:
                spot.park(v)
                return Ticket(v, spot, time.time())
        raise LotFullError()
    def unpark(self, ticket):
        v = ticket.spot.vacate()
        return self._compute_fee(time.time() - ticket.ts)
```

**5. Correctness**

- Lot full → custom `LotFullError` exception
- Invalid ticket → check `ticket.spot.vehicle is ticket.vehicle`
- Concurrent parks → wrap `find_spot + park` in a lock
- Motorcycle in a large spot OK; car in motorcycle spot rejected (`fits()`)

## Cheat-sheet for OOD interview behavior

- **Talk first, code later** — write the class names + relationships on the board before any method body.
- **Justify each pattern** — "I'm using Strategy here so we can add a new pricing rule without touching the lot class" (i.e. cite SOLID).
- **Don't over-engineer** — a Singleton you'll only ever use once isn't worth a `Holder` class. Match scope to interview length.
- **Concurrency questions are common** — at minimum, mention what would need synchronization.

## Practice (typical OOD prompts)

- **Parking Lot** — multi-size vehicles + multi-size spots + multi-floor. *Insight:* `Vehicle` and `ParkingSpot` hierarchies; `Lot` as singleton; `fits()` policy on `Spot`.
- **Elevator System** — multiple elevators + multi-floor requests. *Insight:* `ElevatorController` dispatches `Request` to nearest available `Elevator`; State pattern for elevator (Idle / Up / Down).
- **Library Management** — books, members, loans, reservations. *Insight:* `Book`, `Member`, `Loan`; observer for "book back in stock" notifications.
- **Restaurant Reservation** — tables of various sizes + time slots + waitlist. *Insight:* `Table`, `Reservation`, `Restaurant`; calendar grid + greedy fit.
- **Hotel Reservation** — rooms, dates, pricing tiers. *Insight:* before-during-after pattern (Reserve / Serve / Check Out); Strategy for pricing.
- **Snake & Ladders** — board game with rules and dice. *Insight:* `Game`, `Player`, `Board`, `Dice`; Strategy for dice roll; State for player position.
- **Chess** — pieces with their own move rules. *Insight:* abstract `Piece` with `valid_moves(board)`; concrete subclasses override; `Board` enforces global rules (check, checkmate).
- **Vending Machine** — accept coins, dispense items, give change. *Insight:* State pattern (Idle / HasMoney / Dispensing); inventory management.
- **In-Memory File System** — `mkdir`, `addContent`, `ls`, `read`. *Insight:* trie of path components; node holds children dict + (optional) file content. [LC 588](https://leetcode.com/problems/design-in-memory-file-system/)

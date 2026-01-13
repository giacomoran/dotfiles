## Rule 1. Consistency

Code within a project should be consistent with the rest of the project, even if this means breaking the rules below. Adhere to shared coding standards, style guides, and best practices across the project. Write code that is easy for any team member to read, understand, and modify, ensuring consistent naming conventions, formatting, and patterns. Avoid personal preferences that deviate from the team's agreed standards, and prioritize clarity over cleverness. Aim for simplicity and predictability so that the codebase feels cohesive, regardless of who wrote it, enabling smoother collaboration and long-term maintainability.

## Rule 2. Naming Conventions

Follow a noun-first approach for variables and constants, for example `idChat` instead of `chatId`. Follow a verb-fist approach for functions, for example `computeContentFromTree` or `fetchDataUser`. Notice that we still follow the noun-first approach, it's `fetchDataUser` instead of `fetchUserData`. Plural applies to the noun, for example for multiple user ids use `idsUser` instead of `idsUsers` or `idUsers`.

We use the `bak` prefix/suffix for backup files and folders, ignore those files and folder unless explicitly asked. We use the `tmp` prefix/suffix for temporary files and folders, ignore those files and folder unless explicitly asked. We use the `zxtra` prefix/suffix for extra files and folders, which maybe we are not sure we'll use or that are a work-in-progress, you should generally ignore those as well (`zxtra` is `extra` but starting with the `z`, so that the files and folder appear last in a alphabetically sorted list).

## Rule 3. Nominal Consistency

Align the caller's variable names with the callee's parameter names to reduce cognitive load and make data flow explicit. The variable names outside a function must match the internal parameters exactly. The exception is when handling generic sequences or iterative data, where indexed suffixes (like `_1, _2, _3`) are used to represent distinct instances of the same conceptual type.

Here are some examples:

```python
def calculate_velocity(distance, time):
    return distance / time

distance = 100
time = 20
velocity = calculate_velocity(distance, time)
```

```python
def process_sensor_batch(readings):
    return sum(readings) / len(readings)

# Suffixes used to distinguish distinct readings of the same type
reading_1 = 0.85
reading_2 = 0.92
reading_3 = 0.88

# Passed as a collection to a single parameter
average = process_sensor_batch([reading_1, reading_2, reading_3])
```

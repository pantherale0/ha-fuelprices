# Find fuels from location `find_fuels`

**Name:** Find fuel prices from location

**Description:** This service retrieves all fuel prices for a given location, sorted by the cheapest first.

**Fields:**

| Field      | Description                                     | Required | Selector Type |
|------------|-------------------------------------------------|----------|---------------|
| `location` | The location of the area to search.            | Yes      | Location (with radius) |
| `type`     | The fuel type to search for (such as E5, E10, B7, SDV). | Yes      | Text (single line) |

**Example:**

```yaml
service: fuel_prices.find_fuels
data:
  location:
    latitude: 52.520008
    longitude: 13.404954
    radius: 10
  type: E10
```

This example would find prices for E10 fuel within a 10-mile radius of the given latitude and longitude.

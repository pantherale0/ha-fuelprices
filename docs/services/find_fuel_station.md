# Find fuel stations from locations `find_fuel_station`

**Name:** Find fuel stations from location

**Description:** Find all of the available fuel stations, alongside available fuels and cost for a given location. The results are *not* sorted.

**Fields:**

| Field      | Description                     | Required | Selector Type |
|------------|---------------------------------|----------|---------------|
| `location` | The location of the area to search. | Yes      | Location (with radius) |

**Example:**

```yaml
service: fuel_prices.find_fuel_station
data:
  location:
    latitude: 52.520008
    longitude: 13.404954
    radius: 5
```

This example would find fuel stations within a 5 mile radius of the provided coordinates.

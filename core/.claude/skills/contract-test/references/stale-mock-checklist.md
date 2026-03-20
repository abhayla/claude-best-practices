# Stale Mock Checklist

## Stale Mock Checklist

Provider `<provider-name>` verification revealed changed response shapes.
The following consumer mocks reference affected endpoints and may need updates:

| Consumer | Test File | Line | Endpoint | Stale Field(s) | Action |
|----------|-----------|------|----------|-----------------|--------|
| <consumer-name> | tests/unit/test_inventory_client.py | 34 | GET /api/products/:id/stock | `updatedAt` (type changed) | Update mock return value |
| <consumer-name> | tests/unit/test_order_service.py | 78 | POST /api/orders | `discount` (field added) | Add field to mock response |
| <consumer-name> | __tests__/api/inventory.test.ts | 22 | GET /api/products/:id/stock | `warehouse` (field removed) | Remove field from mock |


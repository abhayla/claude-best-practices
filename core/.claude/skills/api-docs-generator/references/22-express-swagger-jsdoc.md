# 2.2 Express + swagger-jsdoc

### 2.2 Express + swagger-jsdoc

```javascript
// swagger.js
const swaggerJsdoc = require("swagger-jsdoc");

const options = {
  definition: {
    openapi: "3.1.0",
    info: {
      title: "<Project Name> API",
      version: "1.0.0",
      description: "<description>",
    },
    servers: [
      { url: "http://localhost:3000", description: "Development" },
    ],
  },
  apis: ["./src/routes/*.js"],
};

module.exports = swaggerJsdoc(options);
```

Add JSDoc annotations to routes:
```javascript
/**
 * @openapi
 * /users:
 *   post:
 *     summary: Create a new user
 *     tags: [Users]
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/UserCreate'
 *     responses:
 *       201:
 *         description: User created
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/UserResponse'
 *       409:
 *         description: Email already registered
 */
router.post("/users", createUser);
```


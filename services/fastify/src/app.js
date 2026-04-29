const fastify = require("fastify")({ logger: false });
const port = Number(process.env.SERVICE_PORT || 8000);

fastify.get("/ping", async () => ({ status: "ok" }));

fastify.get("/items", async () => ({
  items: Array.from({ length: 100 }, (_, i) => i),
}));

fastify.get("/io", async () => {
  await new Promise((resolve) => setTimeout(resolve, 10));
  return { status: "ok" };
});

fastify.listen({ port, host: "0.0.0.0" });

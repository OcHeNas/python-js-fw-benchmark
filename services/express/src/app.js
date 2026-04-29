const express = require("express");

const app = express();
const port = Number(process.env.SERVICE_PORT || 8000);

app.get("/ping", (req, res) => res.json({ status: "ok" }));

app.get("/items", (req, res) =>
  res.json({ items: Array.from({ length: 100 }, (_, i) => i) })
);

app.get("/io", async (req, res) => {
  await new Promise((resolve) => setTimeout(resolve, 10));
  res.json({ status: "ok" });
});

app.listen(port, "0.0.0.0");

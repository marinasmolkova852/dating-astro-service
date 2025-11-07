import express from "express";
import cors from "cors";
import { init } from "@heyputer/puter.js/src/init.cjs";

const app = express();
app.use(cors());
app.use(express.json());

const puter = init(process.env.AUTH_TOKEN);

app.post("/chat", async (req, res) => {
  try {
    const { messages } = req.body;
    const reply = await puter.ai.chat(messages, { model: "gpt-5-nano"});
    const content = reply.message.content
    res.json({ content });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "AI request failed" });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`AI microservice running on port ${PORT}`));
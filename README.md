# SATHI PDF RAG Chatbot

---

## 🧩 Prerequisites

Before you begin, make sure you have the following installed on your system:

- Python
- Ollama
- Docker

---

## 📥 Clone the Repository

```sh
git clone https://github.com/Mudit-Sengar/SATHI.git
cd sathi
```

---

## 📦 Install Dependencies

Install all required Python libraries:

```sh
pip install -r req.txt
```

---

## 🤖 Pull Ollama Models

Download the necessary Ollama models:

```sh
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

---

## 🐳 Pull Docker Images

Fetch the required Docker images:

```sh
docker pull alpine
docker pull qdrant/qdrant
```

---

## ⚙️ Run Qdrant Docker Container

1. **Create a Docker volume** for persistent Qdrant data:

   ```sh
   docker volume create qdrant_data
   ```

2. **Copy storage data** to the volume:

   ```sh
   docker run --rm -v "$(pwd)/qdrant_storage:/from" -v "qdrant_data:/to" alpine cp -a /from/. /to/
   ```

3. **Start the Qdrant server**:
   ```sh
   docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_data:/qdrant/storage --name qdrant_server qdrant/qdrant
   ```

📔 **If you already have the server setup:**

```sh
docker start qdrant_server
```

🛑 **To stop the server when you're done:**

```sh
docker stop qdrant_server
```

---

## 📚 Data Ingestion

Run the ingestion script whenever you need to process new data:

```py
python ingest.py
```

---

## 💻 Launch the Streamlit Frontend

Start the web interface with:

```py
streamlit run app.py
```

---

## 🎉 You're All Set!

Once everything is running:

- Your **Qdrant** database will be active on port **6333**
- The **Streamlit** app will launch in your browser automatically

---

## 🧠 Notes

- Ensure **Ollama** is running before executing any model-related commands.
- Data inside the `qdrant_data` volume will persist between runs.
- To reset your database, remove the Docker volume:
  ```sh
  docker volume rm qdrant_data
  ```

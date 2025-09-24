# 🚛 Prototipo de Ruteo con Prioridad a Clientes Black  

Este proyecto es un **MVP (prototipo mínimo viable)** que demuestra cómo priorizar clientes **Black** en un sistema de ruteo logístico usando **FastAPI** y **SQLite**.  

Incluye:  
- 📦 Base de datos simple en SQLite  
- ⚡ API con FastAPI (endpoints documentados en Swagger)  
- 🚚 Algoritmo básico de ruteo (clientes Black primero, luego los demás, usando cercanía)  
- 🛠️ Endpoint `/seed` para cargar datos de prueba de inmediato  
- 📨 Colección Postman lista para mostrar en la demo  

---

## 📂 Estructura del proyecto

PROTOTIPO_RUTAS/
│── app.py # API principal con FastAPI
│── requirements.txt # Dependencias del proyecto
│── README.md # Instrucciones y documentación
│── Capstone_Prototipo.postman_collection.json # Colección Postman para probar la API
│── venv/ # (NO se sube a GitHub)
│── mvp.db # (NO se sube a GitHub, se regenera con /seed)
│── .gitignore # Ignorar archivos innecesarios

## 🚀 Instrucciones

1. **Clonar o copiar el proyecto** en tu carpeta local.
2. Crear un entorno virtual:
   ```bash
   python -m venv venv
3. **Activarlo**
  - Windows:
       ```bash
       venv\Scripts\activate
  - Linux / Mac:
       ```bash
       source venv/bin/activate
4. **Instalar dependencias**
   ```bash
      pip install -r requirements.txt
5. **Iniciar el servidor**
   ```bash
   uvicorn app:app --reload

 

# Quint — Learn Investing the Simple Way

## 🧩 Descripción del proyecto

Quint nace para resolver un problema claro: la inversión es percibida como algo complejo, inaccesible y reservado para expertos.
Plataformas profesionales como Bloomberg o Reuters ofrecen herramientas extremadamente potentes, pero su complejidad abruma a cualquier persona sin conocimientos financieros.

La realidad es que la mayoría de la gente no sabe cómo invertir ni cómo tomar decisiones informadas sobre su propio dinero, y por ello terminan recurriendo a instituciones financieras tradicionales para delegar completamente la gestión. Muy pocas personas se sienten capaces de invertir por su cuenta, no por falta de interés, sino por la ausencia de una herramienta que les permita entender, practicar y desarrollar criterio sin riesgo.

Quint propone una alternativa distinta: no pretende replicar plataformas profesionales, sino convertir el aprendizaje financiero en una experiencia simple, visual, guiada e interactiva, casi como un juego.

El objetivo no es invertir dinero real, sino aprender cómo funcionan los mercados, las carteras, el riesgo, la diversificación y los escenarios futuros de forma intuitiva.


## 🎯 Objetivos principales

- Ofrecer una herramienta educativa que **enseñe a invertir sin necesidad de conocimientos previos**.  
- Simplificar conceptos financieros complejos mediante gráficos interactivos, simulaciones y explicaciones claras.  
- Permitir al usuario **crear, analizar y optimizar carteras** de forma sencilla.  
- Mostrar cómo cambian los resultados mediante **visualizaciones comparativas** (cartera actual vs. optimizada).  
- Integrar un módulo de **forecasting** mediante simulaciones Monte Carlo para entender posibles escenarios futuros.  
- Crear una experiencia accesible y pedagógica que sirva como puerta de entrada al mundo de la inversión.

---

## 🛠️ Plan inicial de trabajo

### **Fase 1 — Definición del concepto**
- Identificación de la barrera de entrada al conocimiento financiero.  
- Diseño de Quint como plataforma educativa que simplifica el mundo de las inversiones.  
- División del proyecto en módulos principales: Vista General, Optimización y Forecasting.

---

### **Fase 2 — Backend (FastAPI + Docker)**
- Creación de la arquitectura backend basada en microservicios.  
- Implementación de endpoints para:
  - Gestión de carteras (`/portfolios`)
  - Optimización (`/optimization`)
  - Forecasting (`/forecast/portfolio`)
  - Búsqueda de activos (`/search/ticker`)
- Integración con DuckDB para persistencia y Redis para operaciones intensivas.  
- Contenerización completa mediante Docker.

---

### **Fase 3 — Frontend (Dash)**
- Desarrollo de una interfaz simple e intuitiva basada en Dash.  
- Implementación de las pantallas:
  - **Vista General:** gráficos clave, rendimiento, correlaciones, KPIs.  
  - **Optimización:** comparación entre pesos actuales y optimizados.  
  - **Forecasting:** simulaciones Monte Carlo para visualizar escenarios P5–P50–P95.
- Integración con los endpoints del backend en tiempo real.  
- Uso de ECharts para gráficos interactivos y modernos.

---

### **Fase 4 — Optimización de carteras**
- Implementación de modelos clásicos: Markowitz, mínima volatilidad, máximo Sharpe, etc.  
- Generación automática de comparativas entre cartera actual vs. optimizada.  
- Preparación de gráficos de pesos, rendimiento y riesgo.

---

### **Fase 5 — Forecasting mediante Monte Carlo**
- Cálculo de escenarios futuros para la cartera existente y la optimizada.  
- Visualización de bandas de confianza (P5, P50, P95).  
- Explicaciones simples para interpretar la volatilidad y el riesgo.


### **Fase 6 — Refinamiento y entrega**
- Pruebas finales, validación de datos, control de errores.  
- Ajustes de interfaz y experiencia de usuario.  
- Preparación del entorno final para presentación y documentación.

---

## 📌 Estado actual
El proyecto se encuentra en desarrollo activo, con backend, frontend y módulo de optimización ya integrados.  
La plataforma sigue evolucionando para convertirse en una herramienta educativa financiera completa, sencilla y accesible.

---

## 📎 Licencia
Este proyecto está en fase académica y no cuenta todavía con una licencia pública definida.

---


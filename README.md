# Cartera Inteligente: Visualización y Rebalanceo Predictivo

## Descripción breve
Cuadro de mando completo que permite montar carteras personalizadas, monitorizar
su evolución frente a benchmarks, recibir recomendaciones heurísticas basadas en
momentum, noticias y proyecciones lineales, y explorar predicciones de cada
activo.
Cuadro de mando que monitoriza una cartera, la compara con un benchmark y
sugiere rebalanceos basados en señales predictivas y optimización con
restricciones realistas (costes y rotación), incluyendo backtesting con
validación temporal.

## Objetivos principales
- O1. Monitorizar rendimiento, riesgo y drawdowns de la cartera vs. benchmark.
- O2. Generar señales (momentum, reversión, volatilidad) y predicciones de retornos.
- O3. Optimizar pesos con control de riesgo, límites y costes.
- O4. Explicar las recomendaciones y evaluar la estrategia con backtesting.

## Plan inicial de trabajo
- **Fase 1 — Descubrimiento (Semana 1):** alcance, universo de activos, definición de benchmark, setup de repo y datos.
- **Fase 2 — Datos (Semanas 2‑3):** ingesta/caché de históricos, limpieza, cálculo de retornos y costes supuestos.
- **Fase 3 — Señales y modelo (Semanas 3‑4):** momentum y reversión; regresión regularizada en ventana *rolling*.
- **Fase 4 — Riesgo y optimizador (Semanas 5‑6):** covarianza Ledoit‑Wolf; optimización media‑varianza con límites y penalización de rotación.
- **Fase 5 — Visualización (Semanas 6‑7):** paneles de performance, riesgo, correlaciones, atribución y recomendaciones.
- **Fase 6 — Backtesting y evaluación (Semanas 7‑8):** *walk‑forward*, métricas (Sharpe, Sortino, Calmar, Máx. DD, IR), análisis de sensibilidad.
- **Fase 7 — Entrega (Semana 9):** pulido UI, memoria de 2 páginas y demo.

## Entorno de desarrollo

### Requisitos
Instala las dependencias de Python listadas en `requirements.txt`. Se recomienda
crear un entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Módulos disponibles
- `smart_portfolio_viz.data.yahoo`: utilidades para descargar históricos desde
  Yahoo Finance con validación de entradas y normalización del formato.
- `smart_portfolio_viz.analytics.portfolio`: cálculos de métricas de rendimiento,
  riesgo y comparación con benchmarks, pensados para alimentar el dashboard y
  futuros optimizadores.
- `smart_portfolio_viz.workflows.overview`: orquestación de ingesta + métricas
  para construir un resumen listo para la capa de visualización.
- `smart_portfolio_viz.insights`: heurísticas para clasificar la cartera,
  generar recomendaciones de compra/venta, proponer sustitutos por sector y
  proyectar precios a corto plazo.

### Aplicación Streamlit
Ejecuta la interfaz completa (gráficos de asignación, monitor por activo,
recomendaciones, noticias y predicciones) con:

```bash
streamlit run src/smart_portfolio_viz/app.py
```

La barra lateral permite definir tickers, pesos, rango temporal e intervalo de
datos, así como un benchmark opcional. El dashboard incluye:

- Gráfico circular y tabla comparativa de la asignación de cartera y retornos
  rápidos (1, 5, 30 días, 6 meses y 1 año).
- Monitor por activo con selector de ventana temporal al estilo Yahoo Finance.
- Resumen de performance frente al benchmark, estado de la cartera y proyección
  de 30 días.
- Recomendaciones de compra/venta con sustitutos sugeridos y tabla de precios
  proyectados por activo.
- Sección de noticias con *bullet points* y enlaces directos a las fuentes.

### Ejemplo rápido
```python
from datetime import datetime, timedelta

from smart_portfolio_viz.workflows import OverviewConfig, build_portfolio_overview

config = OverviewConfig(
    tickers=["AAPL", "MSFT", "GOOG"],
    weights={"AAPL": 0.5, "MSFT": 0.3, "GOOG": 0.2},
    start=datetime.utcnow() - timedelta(days=365),
    benchmark="^GSPC",
)
overview = build_portfolio_overview(config)

print("Retorno anualizado: ", overview.performance.annualised_return)
print("Sharpe: ", overview.performance.sharpe_ratio)
print("Contribuciones anualizadas:\n", overview.contributions)
```

Para más contexto sobre la visión y los siguientes pasos, revisa
[`docs/architecture.md`](docs/architecture.md) y la
[`Guía de módulos`](docs/module_overview.md).

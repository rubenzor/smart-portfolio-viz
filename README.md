# Cartera Inteligente: Visualización y Rebalanceo Predictivo

## Descripción breve
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

### Ejemplo rápido
```python
from datetime import datetime, timedelta

from smart_portfolio_viz.data.yahoo import build_price_frame
from smart_portfolio_viz.analytics.portfolio import PortfolioSnapshot, performance

prices = build_price_frame(["AAPL", "MSFT"], start=datetime.utcnow() - timedelta(days=365))
weights = {"AAPL": 0.6, "MSFT": 0.4}
report = performance(PortfolioSnapshot(prices=prices, weights=weights))

print(report.annualised_return)
print(report.sharpe_ratio)
```

Para más contexto sobre la visión y los siguientes pasos, revisa
[`docs/architecture.md`](docs/architecture.md).

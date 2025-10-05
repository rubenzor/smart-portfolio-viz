# Guía de funcionamiento de los módulos

Este documento resume qué hace cada pieza del proyecto y cómo se conectan. La
intención es tener una referencia rápida cuando vayamos añadiendo una interfaz
web y más automatización.

## 1. Ingesta de datos — `smart_portfolio_viz.data`

### `yahoo.PriceRequest`
Estructura de datos (dataclass) que valida los parámetros para pedir históricos
a Yahoo Finance. Normaliza los *tickers* (mayúsculas, sin espacios) y evita
errores comunes al trabajar con formularios.

### `yahoo.download_price_history`
Envuelve a `yfinance.download` para devolver un `DataFrame` con precios
ajustados, limpiando columnas vacías y manteniendo un índice uniforme aunque se
solicite un único activo.

### `yahoo.build_price_frame`
Atajo para quienes solo necesitan pasar tickers y rango temporal. Se utiliza en
los *workflows* para mantener el código legible.

## 2. Analítica de cartera — `smart_portfolio_viz.analytics`

### `portfolio.PortfolioSnapshot`
Agrupa precios, pesos objetivo y un benchmark opcional. Garantiza que los datos
están alineados antes de realizar cálculos.

### `portfolio.performance`
Genera un `PerformanceReport` con métricas clave: retorno total, retorno y
volatilidad anualizados, ratio de Sharpe, drawdown máximo y series acumuladas
para graficar.

### `portfolio.tracking_error` e `information_ratio`
Herramientas para comparar la cartera con su benchmark utilizando retornos
logarítmicos diarios.

## 3. Workflows de orquestación — `smart_portfolio_viz.workflows`

### `overview.OverviewConfig`
Recoge los parámetros de entrada (tickers, pesos, fechas, intervalo, benchmark)
que llegarán desde la UI o un endpoint. Sirve como contrato entre capas.

### `overview.build_portfolio_overview`
Función de alto nivel que coordina la descarga de precios, el cálculo de
retornos y la generación del informe de performance. Devuelve un
`PortfolioOverview` con:

- `prices`: precios ajustados por activo.
- `returns`: retornos logarítmicos diarios.
- `weights`: pesos normalizados.
- `portfolio_returns`: serie temporal del rendimiento de la cartera.
- `performance`: métricas agregadas listas para mostrar.
- `benchmark_returns` y `benchmark_performance`: comparables si se solicita un
  benchmark.
- `contributions`: aportación anualizada de cada activo.
- `correlation_matrix`: matriz de correlaciones para detectar solapamientos.

## 4. Próximos pasos sugeridos

1. **Persistencia y caché:** almacenar descargas en disco/base de datos para no
   saturar la API de Yahoo.
2. **Señales y modelos:** incorporar indicadores técnicos y un pequeño motor de
   predicción para alimentar recomendaciones.
3. **Interfaz web:** construir paneles en *Streamlit* o *FastAPI + React* usando
   `PortfolioOverview` como *payload* principal.

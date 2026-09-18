# Recolector de velas de 1 minuto

Yahoo solo sirve velas de 1 minuto de los últimos 7 días. Este repo las
guarda cada semana para acumular histórico propio.

En tres meses hay unos 60 días de mercado, que es lo mínimo para
investigar la forma del ajuste intradía.

## Puesta en marcha

1. Crea el repo en GitHub y sube estos ficheros.
2. En Settings → Actions → General → Workflow permissions, marca
   **Read and write permissions**. Sin eso el workflow no puede
   guardar los datos.
3. En la pestaña Actions, lanza `recolectar velas de 1 minuto` a mano
   una vez para comprobar que funciona.

Después corre solo los sábados a las 07:00 UTC.

## En local

```bash
pip install -r requirements.txt
python recolector.py              # todos los tickers
python recolector.py MSTR COIN    # solo algunos
```

Ejecutarlo dos veces no duplica nada.

## Qué se guarda

Un CSV por ticker en `datos/`, con timestamp en UTC y precios **sin
ajustar**. Sin ajustar a propósito: es el precio que se opera de verdad,
y así el histórico no cambia hacia atrás cada vez que hay un dividendo.

## Lo que hay que anotar a mano

`registro_manual.csv`. Dos datos que no están en ninguna API gratuita y
que son justo los que faltan para saber si la estrategia tiene margen:

- **Coste de préstamo anual** de cada activo, en la ficha del
  instrumento del bróker. Una vez por semana basta. Interesa sobre todo
  si sube los días que bitcoin cae.
- **Horquilla en la apertura**, mirando el bróker a las 15:30 hora
  española y anotando la diferencia entre compra y venta en los primeros
  minutos. Dos semanas dan idea suficiente.

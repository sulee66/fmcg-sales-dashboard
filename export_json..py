import pandas as pd
import json

print("Membaca file Parquet 1 juta baris...")
df = pd.read_parquet('fmcg_sales_CLEANED.parquet')

# Hitung Gross Profit
df['gross_profit'] = df['net_sales'] - (df['units_sold'] * df['purchase_cost'])

# 1. KPI Totals
total_sales = float(df['net_sales'].sum())
total_profit = float(df['gross_profit'].sum())
margin_pct = float((total_profit / total_sales * 100) if total_sales > 0 else 0)
total_units = float(df['units_sold'].sum())

# 2. Monthly Trend
monthly = df.groupby(['year', 'month'])['net_sales'].sum().reset_index()

# 3. Category Margin
cat = df.groupby('category').agg({'net_sales':'sum', 'gross_profit':'sum'}).reset_index()
cat['margin_pct'] = (cat['gross_profit'] / cat['net_sales']) * 100

# 4. Top 5 Dairy Rugi
dairy = df[df['category'] == 'Dairy'].groupby(['sku_id', 'sku_name'])['gross_profit'].sum().reset_index()
dairy_loss = dairy.sort_values(by='gross_profit', ascending=True).head(5)

# 5. Stock-out per Kota
stock = df[df['stock_out_flag'] == 1].groupby('city').size().reset_index(name='stockout_count').sort_values(by='stockout_count', ascending=False)

# 6. Top 10 Transaksi Rugi
loss_table = df[df['gross_profit'] < 0][['store_id', 'city', 'category', 'sku_name', 'list_price', 'purchase_cost', 'net_sales', 'gross_profit']].head(10).to_dict(orient='records')

data_json = {
    'kpi': {
        'total_sales': total_sales,
        'total_profit': total_profit,
        'margin_pct': margin_pct,
        'total_units': total_units
    },
    'monthly_trend': monthly.to_dict(orient='records'),
    'category_margin': cat.to_dict(orient='records'),
    'dairy_loss': dairy_loss.to_dict(orient='records'),
    'stockout': stock.to_dict(orient='records'),
    'loss_table': loss_table
}

with open('dashboard_data.json', 'w') as f:
    json.dump(data_json, f, indent=4)

print("Selesai! File 'dashboard_data.json' berhasil dibuat dari 1 juta baris data asli!")
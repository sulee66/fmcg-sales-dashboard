import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="FMCG Executive Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom Styling (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 22px; font-weight: bold; }
    .stMetric {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Load Data Parquet
@st.cache_data(ttl=3600)
def load_data():
    file_path = "fmcg_sales_CLEANED.parquet"
    if not os.path.exists(file_path):
        st.error(f"File '{file_path}' gak ketemu!")
        st.stop()
        
    df_data = pd.read_parquet(file_path)
    df_data['gross_profit'] = df_data['net_sales'] - (df_data['units_sold'] * df_data['purchase_cost'])
    return df_data

df = load_data()

# 3. Header
st.title("📊 FMCG Executive Performance Dashboard")
st.caption("Monitoring Real-Time Penjualan, Profit Margin, September Drop, dan Stock-Out")
st.divider()

# 4. Sidebar Filter
st.sidebar.header("🔍 Filter Data")
selected_year = st.sidebar.multiselect("Tahun", sorted(df['year'].unique()), default=list(sorted(df['year'].unique())))
selected_category = st.sidebar.multiselect("Kategori Produk", list(df['category'].unique()), default=list(df['category'].unique()))

df_filtered = df[
    (df['year'].isin(selected_year)) & 
    (df['category'].isin(selected_category))
]

# 5. Top KPI Cards (Otomatis Menyesuaikan Skala Angka)
total_sales = df_filtered['net_sales'].sum()
total_profit = df_filtered['gross_profit'].sum()
margin_pct = (total_profit / total_sales * 100) if total_sales > 0 else 0
total_units = df_filtered['units_sold'].sum()

# Fungsi pembantu format rupiah & unit
def format_rupiah(val):
    if abs(val) >= 1e12:
        return f"Rp {val/1e12:.2f} Triliun"
    elif abs(val) >= 1e9:
        return f"Rp {val/1e9:.2f} Miliar"
    elif abs(val) >= 1e6:
        return f"Rp {val/1e6:.2f} Juta"
    else:
        return f"Rp {val:,.0f}"

def format_unit(val):
    if val >= 1e6:
        return f"{val/1e6:.2f} Juta pcs"
    elif val >= 1e3:
        return f"{val/1e3:.2f} Ribu pcs"
    else:
        return f"{val:,.0f} pcs"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Net Sales", format_rupiah(total_sales))
col2.metric("Total Profit Kotor", format_rupiah(total_profit))
col3.metric("Profit Margin Efektif", f"{margin_pct:.2f}%")
col4.metric("Total Unit Terjual", format_unit(total_units))

st.divider()

# 6. Grafik Utama
col_left, col_right = st.columns([1.3, 1])

with col_left:
    st.subheader("📈 Tren Penjualan Bulanan (September Drop)")
    trend_df = df_filtered.groupby(['year', 'month'])['net_sales'].sum().reset_index()
    fig_line = px.line(
        trend_df, 
        x='month', 
        y='net_sales', 
        color='year', 
        markers=True,
        labels={'net_sales': 'Net Sales (Rp)', 'month': 'Bulan'},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_line.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=1))
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("⚖️ Profit Margin per Kategori")
    cat_df = df_filtered.groupby('category').agg({'net_sales':'sum', 'gross_profit':'sum'}).reset_index()
    cat_df['margin_pct'] = (cat_df['gross_profit'] / cat_df['net_sales']) * 100
    
    fig_bar = px.bar(
        cat_df, 
        x='category', 
        y='margin_pct', 
        text_auto='.1f',
        color='margin_pct',
        color_continuous_scale='Reds_r'
    )
    fig_bar.update_layout(xaxis_title="", yaxis_title="Margin (%)")
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# 7. Grafik Anomali Dairy & Stock-Out Toko
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("⚠️ Top SKU Dairy Rugi Margin (Pricing Error)")
    dairy_df = df_filtered[df_filtered['category'] == 'Dairy'].groupby(['sku_id', 'sku_name'])['gross_profit'].sum().reset_index()
    dairy_loss = dairy_df.sort_values(by='gross_profit', ascending=True).head(5)
    
    fig_dairy = px.bar(
        dairy_loss, 
        x='gross_profit', 
        y='sku_name', 
        orientation='h',
        color_discrete_sequence=['#d9534f'],
        labels={'gross_profit': 'Gross Profit (Rp)', 'sku_name': 'SKU Name'}
    )
    st.plotly_chart(fig_dairy, use_container_width=True)

with col_right2:
    st.subheader("🔴 Frekuensi Kehabisan Stok per Kota (Stock-Out)")
    stock_df = df_filtered[df_filtered['stock_out_flag'] == 1].groupby('city').size().reset_index(name='jumlah_stockout').sort_values(by='jumlah_stockout', ascending=False)
    
    fig_stock = px.bar(
        stock_df, 
        x='city', 
        y='jumlah_stockout', 
        text='jumlah_stockout',
        color_discrete_sequence=['#f0ad4e']
    )
    fig_stock.update_layout(xaxis_title="Kota", yaxis_title="Jumlah Insiden Stock-Out")
    st.plotly_chart(fig_stock, use_container_width=True)

# 8. Tabel Transaksi Rugi
st.divider()
st.subheader("📋 Detail Transaksi Margin Negatif (Rugi)")
loss_table = df_filtered[df_filtered['gross_profit'] < 0][['store_id', 'city', 'category', 'sku_name', 'list_price', 'purchase_cost', 'net_sales', 'gross_profit']]
st.dataframe(loss_table.head(100), use_container_width=True)

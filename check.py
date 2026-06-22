import duckdb
con = duckdb.connect()
df = con.execute("SELECT sum(revenue) as total_revenue, count(*) as total_orders FROM 'd:/projects/ReadOut-B2B-Analytics-SaaS/scripts/demo-sales-orders.csv'").df()
print(df)

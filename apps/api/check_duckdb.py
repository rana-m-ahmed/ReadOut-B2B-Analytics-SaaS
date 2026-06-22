import duckdb
con = duckdb.connect()
df = con.execute("SELECT sum(revenue) as total_revenue, count(*) as total_orders FROM 'd:/projects/ReadOut-B2B-Analytics-SaaS/apps/api/tests/fixtures/demo_data.csv'").df()
print(df)

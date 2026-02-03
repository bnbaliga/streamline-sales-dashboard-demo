import streamlit as st

st.metric(label="Velocity in kilometres per hour", value=75.4, delta=-2)


import streamlit as st
import numpy as np

df = np.random.randn(5,5)

c1, c2, c3 = st.columns(3)

with c1:
	st.markdown("## Line Chart")
	st.line_chart(df)
with c2:
	st.markdown("## Area Chart")
	st.area_chart(df)
with c3:
	st.markdown("## Bar Chart")
	st.bar_chart(df)

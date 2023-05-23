import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
import datetime
import altair as alt
from openpyxl import load_workbook
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objs as go
import plotly.colors as pc
import re
import warnings
import calendar
warnings.filterwarnings('ignore')
import pycountry


st.set_page_config(
    page_title="HWS",
    layout = 'wide',
)
st.title('Hotel Website')

st.subheader('Please Upload Excel Files')
uploaded_files = st.file_uploader("Choose a Excel file",type = 'xlsx', accept_multiple_files=True)
all = []
for uploaded_file in uploaded_files:
    df = pd.read_excel(uploaded_file, thousands=',', skiprows=[0,1,2,3,4,5,6])
    all.append(df)
all = pd.concat(all)

def clean(all):
    all = all.drop(['No.','Stay Month','Day of week','Child Code','Campaign'
                    ,'By Partner','Note','utm_id','utm_term','Guest Name','Email','Room Revenue'], axis=1)
    all[['Gender','Phone']] = all[['Gender','Phone']].fillna('Unknown')
    all[['Payment Gateway','Payment Scheme']] = all[['Payment Gateway','Payment Scheme']].fillna('None')
    all['Access Code'] = all['Access Code'].fillna('Not used')
    all[['Booking Number','Phone']] = all[['Booking Number','Phone']].astype('str')
    all = all.rename(columns={'Campaign.1': 'Campaign','# of night':'LOS','# of room':'Quantity','# of room night':'RN'})
    all = all.fillna('None')
    return all

def convert_to_iso3(country_name):
    try:
        return pycountry.countries.get(name=country_name).alpha_3
    except:
        return None
    
all = clean(all)
def perform(all): 
    all1 = all.copy()
    all1["Check-in"] = pd.to_datetime(all1["Check-in"], format='%d-%m-%Y')
    all1['Booking Date'] = pd.to_datetime(all1['Booking Date'], format='%d-%m-%Y')
    all1["Check-out"] = pd.to_datetime(all1["Check-out"], format='%d-%m-%Y')
    value_ranges = [-1, 0, 1, 2, 3, 4, 5, 6, 7,8, 14, 30, 90, 120]
    labels = ['-one', 'zero', 'one', 'two', 'three', 'four', 'five', 'six','seven', '8-14', '14-30', '31-90', '90-120', '120+']
    all1['Lead time range'] = pd.cut(all1['Lead Time'], bins=value_ranges + [float('inf')], labels=labels, right=False)
    all1['Room'] = all1['Room type'].str.upper()
    all1['ADR'] = (all1['Total Revenue']/all1['LOS'])/all1['Quantity']
    all1['iso_alpha'] =  all1['Booking Location'].apply(convert_to_iso3)
    all1['iso_alpha1'] =  all1['Nationality'].apply(convert_to_iso3)
    return all1

all2 =  perform(all)
channels = all2['Booking Source'].unique()
room_type_options = all2['Room type'].unique().tolist()

selected_channels = st.sidebar.multiselect('Select channels', channels, default=channels)
selected_room_types = st.sidebar.multiselect('Select room types', room_type_options, default=room_type_options)

tab1, tab_stay = st.tabs(['Book on date','Stay on date'])
with tab1:
    if selected_channels:
        filtered_df = all2[all2['Booking Source'].isin(selected_channels)]
        if selected_room_types:
            if 'All' not in selected_room_types:
                filtered_df = filtered_df[filtered_df['Room type'].isin(selected_room_types)]
        else:
            if selected_room_types:
                if 'All' not in selected_room_types:
                    filtered_df = all2[all2['Room type'].isin(selected_room_types)]
    else:
        filtered_df = all2

    month_dict = {v: k for k,v in enumerate(calendar.month_name)}
    months = list(calendar.month_name)[1:]
    selected_month = st.multiselect('Select a month', months)
    if selected_month:
            selected_month_nums = [month_dict[month_name] for month_name in selected_month]
            filtered_df = filtered_df[filtered_df['Booking Date'].dt.month.isin(selected_month_nums)]
    
    col1 , col2 ,col3 = st.columns(3)
    with col2:
        filter_LT = st.checkbox('Filter by LT ')
        if filter_LT:
            min_val, max_val = int(filtered_df['Lead Time'].min()), int(filtered_df['Lead Time'].max())
            LT_min, LT_max = st.slider('Select a range of LT', min_val, max_val, (min_val, max_val))
            filtered_df = filtered_df[(filtered_df['Lead Time'] >= LT_min) & (filtered_df['Lead Time'] <= LT_max)]
        else:
            filtered_df = filtered_df.copy()
    with col1:
        filter_LOS = st.checkbox('Filter by LOS ')
        if filter_LOS:
            min_val, max_val = int(filtered_df['LOS'].min()), int(filtered_df['LOS'].max())
            LOS_min, LOS_max = st.slider('Select a range of LOS', min_val, max_val, (min_val, max_val))
            filtered_df = filtered_df[(filtered_df['LOS'] >= LOS_min) & (filtered_df['LOS'] <= LOS_max)]
        else:   
            filtered_df = filtered_df.copy()
    with col3:
        filter_rn = st.checkbox('Filter by Roomnight')
        if filter_rn:
            min_val, max_val = int(filtered_df['RN'].min()), int(filtered_df['RN'].max())
            rn_min, rn_max = st.slider('Select a range of roomnights', min_val, max_val, (min_val, max_val))
            filtered_df = filtered_df[(filtered_df['RN'] >= rn_min) & (filtered_df['RN'] <= rn_max)]
        else:
            filtered_df = filtered_df.copy()

    counts = filtered_df[['Booking Source', 'Room type']].groupby(['Booking Source', 'Room type']).size().reset_index(name='Count')
    total_count = counts['Count'].sum()

    fig = px.treemap(counts, path=['Booking Source', 'Room type'], values='Count', color='Count',color_continuous_scale='YlOrRd')
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        t1,t2,t3,t4,t5,t6,t7,t8 = st.tabs(['Gender','Nationality','Booking Location'
                                          ,'View Language','View Currency','Booking Status'
                                          ,'Payment Gateway','Payment Scheme'])
        with t1:
            counts = filtered_df['Gender'].value_counts()
            total = counts.sum()
            percentages = counts / total * 100
            fig = go.Figure(go.Bar(
                x=percentages.index,
                y=percentages,
                text=percentages.apply(lambda x: f'{x:.0f}%'),
                ))
            st.plotly_chart(fig,use_container_width=True)
        with t2:
            counts=filtered_df['iso_alpha1'].value_counts().reset_index()
            fig = px.choropleth(counts, locations='count', locationmode='ISO-3', color='iso_alpha1', 
                    color_continuous_scale='YlOrRd')
            st.plotly_chart(fig,use_container_width=True)
        with t3:
            counts=filtered_df['iso_alpha'].value_counts().reset_index()
            fig = px.choropleth(counts, locations='count', locationmode='ISO-3', color='iso_alpha', 
                    color_continuous_scale='YlOrRd')
            st.plotly_chart(fig,use_container_width=True)
        with t4:
            counts = filtered_df['View Language'].value_counts()
            total = counts.sum()
            percentages = counts / total * 100
            fig = go.Figure(go.Bar(
                x=percentages.index,
                y=percentages,
                text=percentages.apply(lambda x: f'{x:.0f}%'),
                ))
            st.plotly_chart(fig,use_container_width=True)
        with t5:
            counts = filtered_df['View Currency'].value_counts()
            total = counts.sum()
            percentages = counts / total * 100
            fig = go.Figure(go.Bar(
                x=percentages.index,
                y=percentages,
                text=percentages.apply(lambda x: f'{x:.0f}%'),
                ))
            st.plotly_chart(fig,use_container_width=True)
        with t6:
            counts = filtered_df['Booking Status'].value_counts()
            total = counts.sum()
            percentages = counts / total * 100
            fig = go.Figure(go.Bar(
                x=percentages.index,
                y=percentages,
                text=percentages.apply(lambda x: f'{x:.0f}%'),
                ))
            st.plotly_chart(fig,use_container_width=True)
        with t7:
            counts = filtered_df['Payment Gateway'].value_counts()
            total = counts.sum()
            percentages = counts / total * 100
            fig = go.Figure(go.Bar(
                x=percentages.index,
                y=percentages,
                text=percentages.apply(lambda x: f'{x:.0f}%'),
                ))
            st.plotly_chart(fig,use_container_width=True)
        with t8:
            counts = filtered_df['Payment Scheme'].value_counts()
            total = counts.sum()
            percentages = counts / total * 100
            fig = go.Figure(go.Bar(
                x=percentages.index,
                y=percentages,
                text=percentages.apply(lambda x: f'{x:.0f}%'),
                ))
            st.plotly_chart(fig,use_container_width=True)

    col1, col2 = st.columns(2)
    channels = filtered_df['Booking Source'].unique()
    num_colors = len(channels)
    colors = px.colors.qualitative.Plotly
    color_scale =  {channel: colors[i % num_colors] for i, channel in enumerate(channels)}
    with col1:
        grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)


    tab1, tab2, tab3 ,tab4, tab5 , tab6 ,tab7= st.tabs(["Average", "Median", "Statistic",'Data'
                                                    ,'Bar Chart','Room roomnight by channel'
                                                    ,'Room revenue by channel'])
    with tab1:
        col0, col1, col2, col4 = st.columns(4)
        filtered_df['total ADR'] = filtered_df["ADR"]*filtered_df["LOS"]*filtered_df["Quantity"]
        col0.metric('**Revenue**',f'{round(filtered_df["total ADR"].sum(),4)}')
        col4.metric('**ADR**',f'{round(filtered_df["ADR"].mean(),4)}',)
        col1.metric("**A.LT**", f'{round(filtered_df["Lead Time"].mean(),4)}')
        col2.metric("**A.LOS**", f'{round(filtered_df["LOS"].mean(),4)}')
    with tab2:
        col1, col2, col3= st.columns(3)
        col4.metric('ADR',f'{round(filtered_df["ADR"].median(),4)}')
        col1.metric("A.LT", f'{round(filtered_df["Lead Time"].median(),4)}')
        col2.metric("A.LOS", f'{round(filtered_df["LOS"].median(),4)}')
    with tab3:
        st.write(filtered_df.describe())
    with tab4:
        st.write(filtered_df)
    with tab5:
        tab11, tab12, tab13, tab14 = st.tabs(['A.LT','A.LOS','A.RN','ADR by month'])
        with tab14:
            month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['ADR'].mean().reset_index()
            mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

            bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='ADR', color='Room type',category_orders={'Booking Date': month_order},
                   text='ADR')
            bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
            st.plotly_chart(bar_chart, use_container_width=True)
        with tab11:
            month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['Lead Time'].mean().reset_index()
            mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

            bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='Lead Time', color='Room type',category_orders={'Booking Date': month_order},
                   text='Lead Time')
            bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
            st.plotly_chart(bar_chart, use_container_width=True)
        with tab12:
            month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['LOS'].mean().reset_index()
            mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

            bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='LOS', color='Room type',category_orders={'Booking Date': month_order},
                   text='LOS')
            bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
            st.plotly_chart(bar_chart, use_container_width=True)
        with tab13:
            month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['RN'].mean().reset_index()
            mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

            bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='RN', color='Room type',category_orders={'Booking Date': month_order},
                   text='RN')
            bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
            st.plotly_chart(bar_chart, use_container_width=True)

    with tab6:
        counts = filtered_df[['Booking Source', 'Room type','RN']].groupby(['Booking Source', 'Room type']).sum().reset_index()
        fig = px.treemap(counts, path=['Booking Source', 'Room type','RN'], values='RN', color='RN',color_continuous_scale='YlOrRd')
        st.plotly_chart(fig,use_container_width=True)
    with tab7:
        counts = filtered_df[['Booking Source', 'Room type','ADR']].groupby(['Booking Source', 'Room type']).sum().reset_index()
        fig = px.treemap(counts, path=['Booking Source', 'Room type','ADR'], values='ADR', color='ADR',color_continuous_scale='YlOrRd')
        st.plotly_chart(fig,use_container_width=True)

    filtered_df['Booking Date'] = pd.to_datetime(filtered_df['Booking Date'])
    filtered_df['Day Name'] = filtered_df['Booking Date'].dt.strftime('%A')
    filtered_df['Week of Year'] = filtered_df['Booking Date'].dt.isocalendar().week


    col1, col2 = st.columns(2)
    with col1:
        st.markdown('**count Booking in week of Year (calendar)**')
        pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size', fill_value=0)
        if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
            pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size', fill_value=0)
            pt = pt[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
            st.write(pt.style.background_gradient(cmap='coolwarm', axis=1))
        else:
            st.write('Not enough data to create a pivot table')

    with col2:
        filtered_df1 =filtered_df[['Booking Date','RN']]
        df_grouped = filtered_df1.groupby('Booking Date').sum().reset_index()
        pivot_df = df_grouped.pivot_table(values='RN'
                                  , index=df_grouped['Booking Date'].dt.isocalendar().week
                                  , columns=df_grouped['Booking Date'].dt.day_name(), aggfunc='sum', fill_value=0)
        st.markdown('**count Roomnight in week of Year (calendar)**')
        if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
            pt = pivot_df[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
            st.write(pt.style.background_gradient(cmap='coolwarm', axis=1))
        else:
            st.write('Not enough data to create a pivot table')

    st.markdown('**LMvsTM**')
    t1,t2 = st.tabs(['Total revenue by roomtype','Total revenue by rate code'])
    with t1:
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        mean_adr_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
        mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

        bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='Total Revenue', color='Room type',category_orders={'Booking Date': month_order},
            text='Total Revenue')
        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
        st.plotly_chart(bar_chart, use_container_width=True)

        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        count_roomtype_by_month = filtered_df.groupby(['Room type', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
        count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

        bar_chart = px.bar(count_roomtype_by_month, x='Booking Date', y='Count', color='Room type', category_orders={'Booking Date': month_order},
                        text='Count')
        bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
        st.plotly_chart(bar_chart, use_container_width=True)
    with t2:
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        mean_adr_by_month = filtered_df.groupby(['Rate Name', filtered_df['Booking Date'].dt.month_name()])['Total Revenue'].sum().reset_index()
        mean_adr_by_month['Booking Date'] = pd.Categorical(mean_adr_by_month['Booking Date'], categories=month_order)

        bar_chart = px.bar(mean_adr_by_month, x='Booking Date', y='Total Revenue', color='Rate Name',category_orders={'Booking Date': month_order},
            text='Total Revenue')
        bar_chart.update_traces(texttemplate='%{text:.2f}', textposition='auto')
        st.plotly_chart(bar_chart, use_container_width=True)

        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        count_roomtype_by_month = filtered_df.groupby(['Rate Name', filtered_df['Booking Date'].dt.month_name()]).size().reset_index(name='Count')
        count_roomtype_by_month['Booking Date'] = pd.Categorical(count_roomtype_by_month['Booking Date'], categories=month_order)

        bar_chart = px.bar(count_roomtype_by_month, x='Booking Date', y='Count', color='Rate Name', category_orders={'Booking Date': month_order},
                        text='Count')
        bar_chart.update_traces(texttemplate='%{text}', textposition='auto')
        st.plotly_chart(bar_chart, use_container_width=True)


    st.markdown('**Pivot table by Booked**')
    t1,t2,t3,t4 = st.tabs(['ADR','LT','LOS','RN'])
    with t1:
        col1, col2 = st.columns(2)
        #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
        col1.markdown('Average ADR by booked and Room Type')
        #st.bar_chart(filtered_df_pi)
        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='ADR', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
        col2.markdown('Average ADR by booked')
        #st.bar_chart(filtered_df_pi)
        adr_avg = filtered_df.groupby(['Booking Date'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='ADR',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['Booking Date', 'ADR']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)
        with col2:
            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)

    with t2:
        col1, col2 = st.columns(2)
        col1.markdown('Average Lead Time by booked and Room Type')
        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['Lead Time'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='Lead Time', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average Lead Time by booked')
        adr_avg = filtered_df.groupby(['Booking Date'])['Lead Time'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='Lead Time',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['Booking Date', 'Lead time range']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='Lead time range',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)
        with col2:
            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)
    with t3:
        col1, col2 = st.columns(2)
        col1.markdown('Average LOS by booked and Room Type')
        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['LOS'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='LOS', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average LOS by booked')
        adr_avg = filtered_df.groupby(['Booking Date'])['LOS'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='LOS',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['Booking Date', 'LOS']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='LOS',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)
        with col2:
            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)
    with t4:
        col1, col2 = st.columns(2)
        col1.markdown('Average RN by booked and Room Type')
        adr_avg = filtered_df.groupby(['Booking Date', 'Room type'])['RN'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='RN', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average RN by booked')
        adr_avg = filtered_df.groupby(['Booking Date'])['RN'].mean().reset_index()
        fig = px.bar(adr_avg, x='Booking Date', y='RN',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['Booking Date', 'RN']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)
        with col2:
            grouped = filtered_df.groupby(['Booking Date', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Booking Date', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig,use_container_width=True)

    st.markdown('**Pivot table by lead time**')
    t1,t2,t3 = st.tabs(['ADR','LOS','RN'])
    with t1:
        col1, col2 = st.columns(2)
        col1.markdown('Average ADR by LT and Room Type')
        adr_avg = filtered_df.groupby(['Lead time range', 'Room type'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='Lead time range', y='ADR', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average ADR by LT')
        adr_avg = filtered_df.groupby(['Lead time range'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='Lead time range', y='ADR',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['Lead time range', 'ADR']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Lead time range', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
    with t2:
        col1, col2 = st.columns(2)
        col1.markdown('Average LOS by LT and Room Type')
        adr_avg = filtered_df.groupby(['Lead time range', 'Room type'])['LOS'].mean().reset_index()
        fig = px.bar(adr_avg, x='Lead time range', y='LOS', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average LOS by LT')
        adr_avg = filtered_df.groupby(['Lead time range'])['LOS'].mean().reset_index()
        fig = px.bar(adr_avg, x='Lead time range', y='LOS',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['Lead time range', 'LOS']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Lead time range', y='counts', color='LOS',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
    with t3:
        col1, col2 = st.columns(2)
        col1.markdown('Average RN by LT and Room Type')
        adr_avg = filtered_df.groupby(['Lead time range', 'Room type'])['RN'].mean().reset_index()
        fig = px.bar(adr_avg, x='Lead time range', y='RN', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average RN by LT')
        adr_avg = filtered_df.groupby(['Lead time range'])['RN'].mean().reset_index()
        fig = px.bar(adr_avg, x='Lead time range', y='RN',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['Lead time range', 'RN']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Lead time range', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)

    st.markdown('**Pivot table by LOS**')
    t1,t2,t3 = st.tabs(['ADR','LT','RN'])
    with t1:
        col1, col2 = st.columns(2)
        col1.markdown('Average ADR by LOS and Room Type')
        adr_avg = filtered_df.groupby(['LOS', 'Room type'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='LOS', y='ADR', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average ADR by LOS')
        adr_avg = filtered_df.groupby(['LOS'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='LOS', y='ADR',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['LOS', 'ADR']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='LOS', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['LOS', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='LOS', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
    with t2:
        col1, col2 = st.columns(2)
        col1.markdown('Average LT by LOS and Room Type')
        adr_avg = filtered_df.groupby(['LOS', 'Room type'])['Lead Time'].mean().reset_index()
        fig = px.bar(adr_avg, x='LOS', y='Lead Time', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average LT by LOS')
        adr_avg = filtered_df.groupby(['LOS'])['Lead Time'].mean().reset_index()
        fig = px.bar(adr_avg, x='LOS', y='Lead Time',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['LOS', 'Lead Time']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='LOS', y='counts', color='Lead Time',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['LOS', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='LOS', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
    with t3:
        col1, col2 = st.columns(2)
        col1.markdown('Average RN by LOS and Room Type')
        adr_avg = filtered_df.groupby(['LOS', 'Room type'])['RN'].mean().reset_index()
        fig = px.bar(adr_avg, x='LOS', y='RN', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average RN by LOS')
        adr_avg = filtered_df.groupby(['LOS'])['RN'].mean().reset_index()
        fig = px.bar(adr_avg, x='LOS', y='RN',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['LOS', 'RN']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='LOS', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['LOS', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='LOS', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)

    st.markdown('**Pivot table by RN**')
    t1,t2,t3 = st.tabs(['ADR','LOS','LT'])
    with t1:
        col1.markdown('Average ADR by RN and Room Type')
        adr_avg = filtered_df.groupby(['RN', 'Room type'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='RN', y='ADR', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average ADR by RN')
        adr_avg = filtered_df.groupby(['RN'])['ADR'].mean().reset_index()
        fig = px.bar(adr_avg, x='RN', y='ADR',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['RN', 'ADR']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='RN', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['RN', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='RN', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
    with t2:
        col1.markdown('Average LOS by RN and Room Type')
        adr_avg = filtered_df.groupby(['RN', 'Room type'])['LOS'].mean().reset_index()
        fig = px.bar(adr_avg, x='RN', y='LOS', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average LOS by RN')
        adr_avg = filtered_df.groupby(['RN'])['LOS'].mean().reset_index()
        fig = px.bar(adr_avg, x='RN', y='LOS',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['RN', 'LOS']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='RN', y='counts', color='LOS',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['RN', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='RN', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
    with t3:
        col1.markdown('Average LT by RN and Room Type')
        adr_avg = filtered_df.groupby(['RN', 'Room type'])['Lead Time'].mean().reset_index()
        fig = px.bar(adr_avg, x='RN', y='Lead Time', color='Room type',text_auto=True)
        fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        col1.plotly_chart(fig, use_container_width=True)
        col2.markdown('Average LT by RN')
        adr_avg = filtered_df.groupby(['RN'])['Lead Time'].mean().reset_index()
        fig = px.bar(adr_avg, x='RN', y='Lead Time',text_auto=True)
        col2.plotly_chart(fig, use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            grouped = filtered_df.groupby(['RN', 'Lead Time']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='RN', y='counts', color='Lead Time',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)
        with col2:
            grouped = filtered_df.groupby(['RN', 'Booking Source']).size().reset_index(name='counts')
            fig = px.bar(grouped, x='RN', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
            st.plotly_chart(fig)


with tab_stay:
    all3 =  perform(all2)
    if selected_channels:
        filtered_df = all3[all3['Booking Source'].isin(selected_channels)]
        if selected_room_types:
            if 'All' not in selected_room_types:
                filtered_df = filtered_df[filtered_df['Room type'].isin(selected_room_types)]
        else:
            if selected_room_types:
                if 'All' not in selected_room_types:
                    filtered_df = all3[all3['Room type'].isin(selected_room_types)]
    else:
        filtered_df = all3

filtered_df['Stay'] = filtered_df.apply(lambda row: pd.date_range(row['Check-in'], row['Check-out']- pd.Timedelta(days=1)), axis=1)
filtered_df = filtered_df.explode('Stay').reset_index(drop=True)
filtered_df = filtered_df[['Stay','Check-in','Check-out','Booking Source','ADR','LOS','Lead Time','Lead time range','RN','Quantity','Room type']]

filtered_df['Day Name'] = filtered_df['Stay'].dt.strftime('%A')
filtered_df['Week of Year'] = filtered_df['Stay'].dt.isocalendar().week
filtered_df = filtered_df.dropna()

month_dict = {v: k for k, v in enumerate(calendar.month_name)}
months = list(calendar.month_name)[1:]
selected_month = st.multiselect('Select a month stay', months)

# Assuming you have a select year input stored in the variable 'selected_year'
selected_year = st.selectbox('Select a year', ['2022', '2023', '2024','2025','2026'], index=1)

if selected_month and selected_year:
    selected_month_nums = [month_dict[month_name] for month_name in selected_month]
    filtered_df = filtered_df[
        (filtered_df['Stay'].dt.month.isin(selected_month_nums)) &
        (filtered_df['Stay'].dt.year == int(selected_year))
    ]
elif selected_month:
    selected_month_nums = [month_dict[month_name] for month_name in selected_month]
    filtered_df = filtered_df[filtered_df['Stay'].dt.month.isin(selected_month_nums)]
elif selected_year:
    filtered_df = filtered_df[filtered_df['Stay'].dt.year == int(selected_year)]
    

col1 , col2 = st.columns(2)
with col2:
    filter_LT = st.checkbox('Filter by LT')
    if filter_LT:
        min_val, max_val = int(filtered_df['Lead Time'].min()), int(filtered_df['Lead Time'].max())
        LT_min, LT_max = st.slider('Select a range of LT', min_val, max_val, (min_val, max_val))
        filtered_df = filtered_df[(filtered_df['Lead Time'] >= LT_min) & (filtered_df['Lead Time'] <= LT_max)]
    else:
        filtered_df = filtered_df.copy()
with col1:
    filter_LOS = st.checkbox('Filter by LOS')
    if filter_LOS:
        min_val, max_val = int(filtered_df['LOS'].min()), int(filtered_df['LOS'].max())
        LOS_min, LOS_max = st.slider('Select a range of LOS', min_val, max_val, (min_val, max_val))
        filtered_df = filtered_df[(filtered_df['LOS'] >= LOS_min) & (filtered_df['LOS'] <= LOS_max)]
    else:
        filtered_df = filtered_df.copy()

st.markdown('**avg ADR without comm and ABF by channal and room type (if you do not filter month, it would be all month)**')
df_january = filtered_df[['Stay','Booking Source','Room type','ADR']]
avg_adr = df_january.groupby(['Booking Source', 'Room type'])['ADR'].mean()
result = avg_adr.reset_index().pivot_table(values='ADR', index='Booking Source', columns='Room type', fill_value='none')
col1, col2, col3 = st.columns(3)
result = result.applymap(lambda x: '{:.2f}'.format(x) if x != 'none' else 'none')
col2.write(result,use_container_width=True)

st.markdown('**You can zoom in**')
col1, col2 = st.columns(2)
channels = filtered_df['Booking Source'].unique()
num_colors = len(channels)
colors = px.colors.qualitative.Plotly
color_scale =  {channel: colors[i % num_colors] for i, channel in enumerate(channels)}
with col1:
    grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
    fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
    st.plotly_chart(fig)
with col2:
    grouped = filtered_df.groupby(['Lead time range', 'Booking Source']).size().reset_index(name='counts')
    fig = px.bar(grouped, x='Lead time range', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
    st.plotly_chart(fig)

col1, col2 = st.columns(2)
with col1:
    st.markdown('**count Stay in week of Year (calendar)**')
    pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size')
    if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
        pt = filtered_df.pivot_table(index='Week of Year', columns='Day Name', aggfunc='size', fill_value=0)
        pt = pt[['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
        st.write(pt.style.background_gradient(cmap='coolwarm', axis=1))
    else:
        st.write('Not enough data to create a pivot table')
with col2:
    st.markdown('**A.LT that Check-in in week of Year (calendar)**')
    grouped = filtered_df.groupby(['Week of Year', 'Day Name'])
    averages = grouped['Lead Time'].mean().reset_index()
    pt = pd.pivot_table(averages, values='Lead Time', index=['Week of Year'], columns=['Day Name'])
    if set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']).issubset(filtered_df['Day Name'].unique()):
        pt = pt.loc[:, ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
        st.write(pt.style.format("{:.2f}").background_gradient(cmap='coolwarm', axis=1))
    else:
        st.write('Not enough data to create a pivot table')

st.markdown('**Pivot table by Stay**')
t1,t2,t3,t4 = st.tabs(['ADR','LT','LOS','RN'])
with t1:
    col1, col2 = st.columns(2)
    #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
    col1.markdown('Average ADR by Stay and Room Type')
    #st.bar_chart(filtered_df_pi)
    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['ADR'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='ADR', color='Room type',text_auto=True)
    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    col1.plotly_chart(fig, use_container_width=True)
    #filtered_df_pi = pd.pivot_table(filtered_df, index='Booked',values=['ADR'])
    col2.markdown('Average ADR by Stay')
    #st.bar_chart(filtered_df_pi)
    adr_avg = filtered_df.groupby(['Stay'])['ADR'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='ADR',text_auto=True)
    col2.plotly_chart(fig, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        grouped = filtered_df.groupby(['Stay', 'ADR']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='ADR',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)

with t2:
    col1, col2 = st.columns(2)
    col1.markdown('Average Lead Time by Stay and Room Type')
    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['Lead Time'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='Lead Time', color='Room type',text_auto=True)
    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    col1.plotly_chart(fig, use_container_width=True)
    col2.markdown('Average Lead Time by Stay')
    adr_avg = filtered_df.groupby(['Stay'])['Lead Time'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='Lead Time',text_auto=True)
    col2.plotly_chart(fig, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        grouped = filtered_df.groupby(['Stay', 'Lead time range']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='Lead time range',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)
with t3:
    col1, col2 = st.columns(2)
    col1.markdown('Average LOS by Stay and Room Type')
    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['LOS'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='LOS', color='Room type',text_auto=True)
    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    col1.plotly_chart(fig, use_container_width=True)
    col2.markdown('Average LOS by Stay')
    adr_avg = filtered_df.groupby(['Stay'])['LOS'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='LOS',text_auto=True)
    col2.plotly_chart(fig, use_container_width=True)
        
    col1, col2 = st.columns(2)
    with col1:
        grouped = filtered_df.groupby(['Stay', 'LOS']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='LOS',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)
with t4:
    col1, col2 = st.columns(2)
    col1.markdown('Average RN by Stay and Room Type')
    adr_avg = filtered_df.groupby(['Stay', 'Room type'])['RN'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='RN', color='Room type',text_auto=True)
    fig.update_layout(legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    col1.plotly_chart(fig, use_container_width=True)
    col2.markdown('Average RN by Stay')
    adr_avg = filtered_df.groupby(['Stay'])['RN'].mean().reset_index()
    fig = px.bar(adr_avg, x='Stay', y='RN',text_auto=True)
    col2.plotly_chart(fig, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        grouped = filtered_df.groupby(['Stay', 'RN']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='RN',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)
    with col2:
        grouped = filtered_df.groupby(['Stay', 'Booking Source']).size().reset_index(name='counts')
        fig = px.bar(grouped, x='Stay', y='counts', color='Booking Source',color_discrete_map=color_scale, barmode='stack')
        st.plotly_chart(fig,use_container_width=True)

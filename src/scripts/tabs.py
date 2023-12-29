def building_data(self):
        selected_gdf = self.filtered_gdf.loc[self.filtered_gdf["scenario_navn"] == "Referansesituasjon"]
        areal = (int(np.sum(selected_gdf['bruksareal_totaltcd..'])))
        st.metric(label = "Areal", value = f"{areal:,} m²".replace(",", " "))
        electric_demand = (int(np.sum(selected_gdf['_elspesifikt_energibehov_sum'])*1000 * 1000))
        st.metric(label = "Elspesifikt behov", value = f"{round(electric_demand, -3):,} kWh".replace(",", " "))
        space_heating_demand = (int(np.sum(selected_gdf['_termisk_energibehov_sum'])*1000 * 1000))
        st.metric(label = "Oppvarmingsbehov", value = f"{round(space_heating_demand, -3):,} kWh".replace(",", " "))
        total_demand = space_heating_demand + electric_demand
        st.metric(label = "Totalt", value = f"{round(total_demand, -3):,} kWh".replace(",", " "))
        df = self.filtered_gdf.drop(columns='geometry')
        df = df.loc[df["scenario_navn"] == "Referansesituasjon"]
        pie_fig = px.pie(data_frame=df, names = 'BYGNINGSTYPE_NAVN')
        # Customize the layout for the pie chart
        pie_fig.update_layout(
            showlegend = False,
            #legend=dict(orientation="h"),
            autosize=False,
            margin=dict(l=0, r=0, b=0, t=0, pad=0),
            #plot_bgcolor="white",
            #legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
        )
        pie_fig.update_traces(
            hoverinfo='label+percent+name', 
            #textinfo = "none"
            )
        st.plotly_chart(pie_fig, use_container_width=True, config={'displayModeBar': False})
        with st.expander("Alle data"):
            st.dataframe(df)
            
    def costs(self):
        i = 0
        for column in self.df_timedata.columns:
            if (i % 2):
                col = c1
            else:
                c1, c2 = st.columns(2)
                col = c2
            with col:
                energy = int(round(np.sum(self.df_timedata[column]), -3))
                effect = int(round(np.max(self.df_timedata[column]), 1))
                cost = int(round(energy * self.elprice))
                st.metric(label = column, value = f"{cost:,} kr/år".replace(",", " "))
                st.caption(f"{energy:,} kWh/år | {effect:,} kW".replace(",", " "))
            i = i + 1
            
    def plot_varighetskurve(self, df, color_sequence, y_min = 0, y_max = None):
        df = self.__sort_columns_high_to_low(df)
        fig = px.line(df, x=df.index, y=df.columns, color_discrete_sequence=color_sequence)
        fig.update_layout(
            legend=dict(yanchor="top", y=0.98, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)")
            )
        fig.update_traces(
            line=dict(
                width=1, 
            ))
        fig.update_xaxes(
            range=[0, 8760],
            title_text='Varighet [timer]',
            mirror=True,
            ticks="outside",
            showline=True,
            linecolor="black",
            gridcolor="lightgrey",
            )
        fig["data"][0]["showlegend"] = True
        fig.update_layout(
            height = 600,
            margin=dict(l=50,r=50,b=10,t=10,pad=0),
            legend={'title_text':''},
            barmode="stack", 
            #plot_bgcolor="white", paper_bgcolor="white",
            legend_traceorder="reversed",
            )
        fig.update_yaxes(
            range=[y_min, y_max],
            title_text='Effekt [kW]',
            mirror=True,
            ticks="outside",
            showline=True,
            linecolor="black",
            gridcolor="lightgrey",
        )
        st.plotly_chart(figure_or_data = fig, use_container_width = True, config = {'displayModeBar': False})

    def __reorder_dataframe(self, df):
        reference_row = df[df['scenario_navn'] == 'Referansesituasjon']
        other_rows = df[df['scenario_navn'] != 'Referansesituasjon']
        reordered_df = pd.concat([reference_row, other_rows])
        reordered_df.reset_index(drop=True, inplace=True)
        return reordered_df

    def plot_bar_chart(self, df, y_max, yaxis_title, y_field, chart_title, scaling_value, color_sequence, percentage_mode = False, fixed_mode = True):
        df[y_field] = df[y_field] * scaling_value
        df = df.groupby('scenario_navn')[y_field].sum().reset_index()
        df = self.__reorder_dataframe(df)
        df["prosent"] = (df[y_field] / df.iloc[0][y_field]) * 100
        df["prosent"] = df["prosent"].round(0)
        if fixed_mode == True:
            y_max = None
        if percentage_mode == True:
            y_field = "prosent"
            y_max = 100
            yaxis_title = "Prosentandel (%)"
        fig = px.bar(df, x='scenario_navn', y=df[y_field], title = f"{chart_title}", color = 'scenario_navn', color_discrete_sequence = color_sequence)
        fig.update_layout(
            showlegend = False,
            margin=dict(l=0,r=0,b=0,t=50,pad=0),
            height=600,
            yaxis_title=yaxis_title,
            xaxis_title="",
            #plot_bgcolor="white",
            legend=dict(yanchor="top", y=0.98, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)"),
            barmode="stack")
        fig.update_xaxes(
                ticks="outside",
                linecolor="black",
                gridcolor="lightgrey",
                tickangle=90
            )
        fig.update_yaxes(
            range=[0, y_max],
            tickformat=",",
            ticks="outside",
            linecolor="black",
            gridcolor="lightgrey",
        )
        if percentage_mode == True:
            fig.update_layout(separators="* .*")
            fig.update_traces(
            hovertemplate='%{y:.0f}%',  # Display percentage values with two decimal places in the tooltip
            )
        else:
            fig.update_layout(separators="* .*")
        st.plotly_chart(figure_or_data = fig, use_container_width = True, config = {'displayModeBar': False})
    
    def plot_timedata(self, df, color_sequence, y_min = 0, y_max = None):
        num_series = df.shape[1]
        plot_rows=num_series
        plot_cols=1
        lst1 = list(range(1,plot_rows+1))
        lst2 = list(range(1,plot_cols+1))
        fig = make_subplots(rows=num_series, shared_xaxes=True, cols=1, insets=[{'l': 0.1, 'b': 0.1, 'h':1}])
        x = 1
        y_old_max = 0
        for i in lst1:
            for j in lst2:
                fig.add_trace(go.Scatter(x=df.index, y=df[df.columns[x-1]].values,name = df.columns[x-1],mode = 'lines', line=dict(color=color_sequence[x-1], width=0.5)),row=x,col=1)
                y_max_column = np.max(df[df.columns[x-1]])
                if y_max_column > y_old_max:
                    y_old_max = y_max_column
                x=x+1
        y_max = y_old_max * 1.1

        fig.update_layout(
            height=600, 
            showlegend=False,
            margin=dict(l=50,r=50,b=10,t=10,pad=0)
            )

        for i in range(num_series):
            fig.update_xaxes(
                tickmode = 'array',
                tickvals = [0, 24 * (31), 24 * (31 + 28), 24 * (31 + 28 + 31), 24 * (31 + 28 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30), 24 * (31 + 28 + 31 + 30 + 31 + 30 + 31 + 31 + 30 + 31 + 30 + 31)],
                ticktext = ["1.jan", "", "1.mar", "", "1.mai", "", "1.jul", "", "1.sep", "", "1.nov", "", "1.jan"],
                row=i + 1, 
                col=1,
                mirror=True,
                ticks="outside",
                showline=True,
                linecolor="black",
                gridcolor="lightgrey",)
            fig.update_yaxes(
                row=i + 1, 
                col=1,
                range=[y_min, y_max],
                title_text='Effekt [kW]',
                mirror=True,
                ticks="outside",
                showline=True,
                linecolor="black",
                gridcolor="lightgrey",
            )
        st.plotly_chart(figure_or_data = fig, use_container_width = True, config = {'displayModeBar': False})

    def __sort_columns_high_to_low(self, df):
        sorted_df = df.apply(lambda col: col.sort_values(ascending=False).reset_index(drop=True))
        return sorted_df
            
    def tabs(self):
        if (len(self.filtered_gdf)) == 0:
            st.warning('Du er utenfor kartutsnittet', icon="⚠️")
            st.stop()
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Effekt", "Energi", "Timedata", "Varighetskurve", "Strømkostnader", "Bygningsinformasjon"])
        with tab1:
            self.plot_bar_chart(df = self.filtered_gdf, y_max = 4500, yaxis_title = "Effekt [kW]", y_field = '_nettutveksling_vintereffekt', chart_title = "Maksimalt behov for tilført el-effekt fra el-nettet", scaling_value = 1000, color_sequence=self.color_sequence, percentage_mode = self.percentage_mode_option)
        with tab2:
            self.plot_bar_chart(df = self.filtered_gdf, y_max = 16000000, yaxis_title = "Energi [kWh/år]", y_field = '_nettutveksling_energi', chart_title = "Behov for tilført el-energi fra el-nettet", scaling_value = 1000 * 1000, color_sequence=self.color_sequence, percentage_mode = self.percentage_mode_option)
        with tab3:
            self.plot_timedata(df = self.df_timedata, color_sequence = self.color_sequence, y_min = 0, y_max = None)
        with tab4:
            self.plot_varighetskurve(df = self.df_timedata, color_sequence = self.color_sequence, y_min = 0, y_max = None)
        with tab5:
            self.costs()
        with tab6:
            self.building_data()
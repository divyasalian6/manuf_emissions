# ============================================================
#  DECOUPLING PLOT (polished) — GDP vs. Carbon Intensity of GDP
#  India / China / USA / Europe, 1990-2024
#  Down-and-right path = economy grows while getting cleaner per $
# ============================================================
library(tidyverse)

panel <- read_csv("combined_tidy_panel_ICUE.csv") %>%
  mutate(place = case_when(
    iso3 == "IND" | country == "India" ~ "India",
    iso3 == "CHN" | str_detect(country, "China") ~ "China",
    iso3 == "USA" | str_detect(country, "United States") ~ "USA",
    TRUE ~ "Europe"
  ))

# --- Reshape: one column for GDP, one for intensity ---------
wide <- panel %>%
  filter(source == "main_mfg_ems",
         indicator %in% c(
           "GDP (constant 2015 US$)",
           "Carbon intensity of GDP (kg CO2e per constant 2015 US$ of GDP)"
         )) %>%
  mutate(metric = if_else(str_detect(indicator, "Carbon intensity"),
                          "intensity", "gdp")) %>%
  select(place, year, metric, value) %>%
  pivot_wider(names_from = metric, values_from = value) %>%
  filter(!is.na(gdp), !is.na(intensity)) %>%
  arrange(place, year)          # IMPORTANT: order by year so the path connects correctly

# --- Helper tables for the start dot, end dot, and end label ---
starts <- wide %>% group_by(place) %>% slice_min(year) %>% ungroup()
ends   <- wide %>% group_by(place) %>% slice_max(year) %>% ungroup()

# --- Build the plot -----------------------------------------
ggplot(wide, aes(x = gdp, y = intensity, color = place)) +
  geom_path(linewidth = 1.1, alpha = 0.9) +                 # the trajectory
  geom_point(data = starts, size = 2, shape = 1) +          # hollow dot = 1990 start
  geom_point(data = ends, size = 3) +                       # solid dot = 2024 end
  geom_text(data = ends, aes(label = place),                # country name at the end
            hjust = -0.15, fontface = "bold", size = 4) +
  scale_x_log10(labels = scales::label_number(
    scale_cut = scales::cut_short_scale())) +               # 2.3e13 -> "23T"
  scale_color_brewer(palette = "Set1") +                    # nicer color set
  expand_limits(x = max(wide$gdp) * 2.2) +                  # room for the labels
  labs(
    title = "Economic growth vs. carbon intensity, 1990-2024",
    subtitle = "Each path runs 1990 (hollow dot) to 2024 (solid dot). Down-and-right = growing while getting cleaner.",
    x = "GDP (constant 2015 US$, log scale)",
    y = "Carbon intensity (kg CO2e per $ of GDP)",
    caption = "Source: World Bank"
  ) +
  theme_minimal(base_size = 13) +
  theme(
    legend.position = "none",                               # labels replace the legend
    plot.title = element_text(face = "bold"),
    plot.subtitle = element_text(color = "grey30"),
    panel.grid.minor = element_blank()
  )


# Save a high-resolution copy for a report or slide:
ggsave("decoupling_plot.png", width = 9, height = 6, dpi = 300)
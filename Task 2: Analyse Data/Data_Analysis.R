# Package
library(tidyverse)

# Data manipulation
Rating <- Rating %>%
  mutate(highlights = replace_na(highlights, replace = 'Not shown'),
         highlights = recode(highlights, 'Highlights' = 'Shown')) %>%
  mutate(overall_rating = as.factor(overall_rating))

Review <- Review[, -(10:33)]
Review <- Review %>%
  mutate(reviewer_num_reviews = replace_na(reviewer_num_reviews, replace = 0),
         reviewer_rating = as.factor(reviewer_rating))

# Exploratory data analysis
  # Categorical variables: Bar chart
    ## Function 
    bar_chart <- function(groupby_variable) {
      Rating %>%
        group_by({{groupby_variable}}) %>% nest() %>%
        mutate(n = map(data, ~ nrow(.x))) %>%
        ggplot(aes(x = {{groupby_variable}}, y = n)) + geom_col()
    }
    ## Overall ratings
    bar_chart(overall_rating)
    ## Price range
    bar_chart(price_range)
    ## Highlights
    bar_chart(highlights)
    
  # Continuous variables: Histogram
    ## Function
    histogram <- function(x_variable) {
      Rating %>%
        ggplot(aes(x = {{x_variable}})) + geom_histogram()
    }
    
    summary_stat <- function(variable) {
      Rating %>%
        select({{variable}}) %>%
        summary()
    }
    ## Number of reviews
    histogram(num_reviews)
    summary_stat(num_reviews)
    ## Number of photos
    histogram(num_photos)
    summary_stat(num_photos)

# Regression analysis
  # Subset the data based on the price range
    # Initialize an empty list
    list_dfs <- vector(mode = "list", length = 4)
    # Append the filtered dataframe to a list structure
    for(i in 1:4) {
      list_dfs[i] <- Rating %>%
        filter(price_range == paste(rep('$', i), collapse = '')) %>% list()
    }
  # Multinomial logistic regression
    # Concept
      # Model nominal outcome variables
      # Log odds of the outcomes ~ Linear combination of the predictor variables
    # Steps
      # Choose the baseline level outcome
      Rating$overall_rating <- relevel(Rating$overall_rating, ref = '3')
      Review$reviewer_rating <- relevel(Review$reviewer_rating, ref = '1')
      # Run the multinomial logistic regression
      library(nnet)
      multinom_model_obj <- compose(summary, multinom)
      model_summary_1 <- multinom_model_obj(overall_rating ~ num_reviews + 
                                                             num_photos + 
                                                             highlights, data = Rating)
      model_summary_2 <- multinom_model_obj(reviewer_rating ~ reviewer_num_friends + 
                                                              reviewer_num_photos + 
                                                              reviewer_num_reviews + 
                                                              str_count(reviewer_text, '\\w+'), data = Review)
      # Interpret coefficients
        # Log-odds
          # A one-unit increase in the variable num_reviews is associated with the decrease in the log odds of being rated as 3.5 vs. 3.0 in the amount of 0.01850317.
          # A one-unit increase in the variable num_photos is associated with the increase in the log odds of being rated as 3.5 vs. 3.0 in the amount of 0.02157272.
          # The log odds of being rated as 3.5 vs. 3.0 will decrease by 18.03622 if moving from no highlights to highlights.
        # Odd-ratios
          # The odd ratio for a one-unit increase in the variable num_reviews is 0.9816670 for being rated as 3.5 vs. 3.0.
          # The odd ratio for a one-unit increase in the variable num_photos is 1.021807 for being rated as 3.5 vs. 3.0. 
          # The odd ratio moving from no highlights to highlights is 0 for being rated as 3.5 vs. 3.0. 
          multinom_model_or <- compose(exp, coef)
          model_or_1 <- multinom_model_or(model_summary_1)
          model_or_2 <- multinom_model_or(model_summary_2)
      # Calculate p-values
      p_value <- function(model_summary) {
        z <- model_summary$coefficients / model_summary$standard.errors 
        return((1 - pnorm(abs(z), 0, 1)) * 2)
      }
      p_value(model_summary_1)
      p_value(model_summary_2)
      # Calculate predicted probability
      fitted(model_summary_1)
      fitted(model_summary_2)
      
    
  
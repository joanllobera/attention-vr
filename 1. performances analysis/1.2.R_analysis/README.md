### R-analysis : Data Analysis on Reaction Times and Accuracy, Plots Included

### Overview
This R script performs a detailed analysis of behavioral data, focusing on reaction times (RTs) and accuracy in a cueing task with distractors. The script includes data cleaning, descriptive statistics, linear mixed-effects models, repeated-measures ANOVAs, post-hoc comparisons, and visualization of results. Analyses are conducted globally, as well as separately for front and rear positions.

The analysis includes:
    - Descriptive statistics by cue, position, and distractor.
    - Linear mixed models and repeated-measures ANOVAs for reaction time and accuracy.
    - Post-hoc comparisons using estimated marginal means.
    - Visualization of results with ggplot2, including jittered points, error bars, and half-eye plots for distributions.

## Libraries

The script uses the following R packages:

    -Data Handling & Cleaning: readxl, readr, dplyr, writexl
    -Statistics:
            - Linear mixed models: lme4, lmerTest
            - ANOVA: afex, ez
            - Regression tools: car
            - Post-hoc comparisons: emmeans
            - Effect sizes: effectsize, sjstats
            - Model diagnostics: DHARMa
            - Descriptive stats: psych
    -Visualization: ggplot2, ggdist, gghalves, ggpubr, patchwork, cowplot, visreg, MuMIn

## Data frames
The script uses multiple data frames for reaction times and accuracy, often subsetted by position, cue, or distractor:

**Accuracy Data** :

    - df_accuracy                              #full dataset of accuracy.
    - df_acc_front                             #accuracy for front position.
    - df_acc_rear                              #accuracy for rear position.
    - df_acc_valid_rear / df_acc_invalid_rear  #rear trials filtered by cue validity.
    - df_recat_acc                             #accuracy data with distractors recategorized (Present vs. Absent).

**Reaction Time Data** :

    - df_success_trials                         # full dataset of reaction times for correct trials.
    - Subsets by cue and position:
        - df_RT_front, df_RT_rear               # Reaction times separataed front/rear
        - df_RT_front_val, df_RT_front_inv      # Reaction times for front vaild trials / front invalid trials
        - df_RT_rear_val, df_RT_rear_inv        # RT for rear valid trials / rer invalid trials
        - df_recategorized_RT_front             # Front trials with distractors recategorized to "Present" or "Absent".

## Analysis

    - Descriptive statistics for RT and accuracy 
    - Repeated-measures ANOVA:
        - Reaction time: factors = cue, position, distractor 
        - Accuracy: same factors.
        
    - Post-hoc comparisons using linear mixed-effects models (lmer) and emmeans.
        - Conducted for cue, distractor, and position effects with participants entered as random effects


    
## VP Example using Kaggle titanic data.
## Run with `Rscript titanic/vrhino/titanic.R`

start <- Sys.time()
model <- vrhino::logistic_regression(name = "Titanic", passes = 3, quadratic = "ff", l1 = 0.001)
results <- model$run("titanic/data/titanic.csv",
              line_function = function(item) {
                  item <- strsplit(item, ",")[[1]]
                  features <- list(paste0("passenger_class_", vrhino::clean(item[[3]])),
                                   paste0("last_name_", vrhino::clean(item[[4]])),
                                   "gender" = if (identical(item[[6]], "male")) { 0 } else { 1 },
                                   "siblings_onboard" = as.numeric(item[[8]]),
                                   "family_members_onboard" = as.numeric(item[[9]]),
                                   "fare" = as.numeric(item[[11]]),
                                   paste0("embarked_", vrhino::clean(item[[13]])))
                  title <- strsplit(item[[5]], ' ')[[1]]
                  if (length(title)) { features <- c(features, paste0("title_", title)) }
                  age <- item[[7]]
                  if (!is.na(is.numeric(age))) { features$age <- as.numeric(age) }
                  list('label' = if (identical(item[[2]]), "1") { 1 } else { 0 },
                       'f' = features)
              },
              evaluate_function = auc)

auc <- paste("AUC:", vrhino::auc(results))
end <- Sys.time()
time <- paste("Time:", end - start)
num_lines <- vrhino::count_lines("titanic/data/titanic.csv")
speed <- paste("Speed:", as.numeric(end - start) * 1000000 / num_lines, "mcs/row")
title <- "TITANIC IN VRHINO"
for (line in paste0(c("", title, Sys.time(), auc, time, speed), "\n")) {
  write(line, file = "test_results.txt", append = TRUE)
}
print(auc)
print(time)
print(speed)

## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit an XGB to the data, get test AUC.

## Import
timer_start <- Sys.time()
titanic <- readr::read_csv("../data/titanic.csv")

## Impute NAs with Median
sapply(titanic, function(col) sum(surveytools2::is.na_like(col)))
# PassengerId    Survived      Pclass        Name         Sex         Age
#           0           0           0           0           0         177
#       SibSp       Parch      Ticket        Fare       Cabin    Embarked
#           0           0           0           0         687           2

mode <- function(x) {
  ux <- unique(x)
  ux[which.max(tabulate(match(x, ux)))]
}

impute <- function(col) {
  value <- if (is.numeric(col)) { median(col, na.rm = TRUE) }
  else { mode(col[!surveytools2::is.na_like(col)]) }
  col[surveytools2::is.na_like(col)] <- value
  col
}

titanic <- data.frame(sapply(titanic, impute))

sapply(titanic, function(col) sum(surveytools2::is.na_like(col)))
# PassengerId    Survived      Pclass        Name         Sex         Age
#           0           0           0           0           0           0
#       SibSp       Parch      Ticket        Fare       Cabin    Embarked
#           0           0           0           0           0           0


## Create Title Feature

split_to_title <- function(x) {
  strsplit(x, split='[.,]')[[1]][2]
}
titanic$Title <- sapply(as.character(titanic$Name), split_to_title)
titanic$Title <- sub(' ', '', titanic$Title)
titanic$Title[titanic$Title %in% c("Mme", "Mlle")] <- 'Mlle'
titanic$Title[titanic$Title %in% c('Capt', 'Don', 'Major', 'Sir')] <- 'Sir'
titanic$Title[titanic$Title %in% c('Dona', 'Lady', 'the Countess', 'Jonkheer')] <- 'Lady'
titanic$Title <- factor(titanic$Title)

table(titanic$Title)
# Col     Dr   Lady Master   Miss   Mlle     Mr    Mrs     Ms    Rev    Sir
#   2      7      3     40    182      3    517    125      1      6      5



## Fit XGB

#### Clean Data for XGB
dep_var <- titanic$Survived
titanic <- dplyr::select(titanic, -PassengerId, -Survived, -Name, -Ticket, -Cabin)

for (numeric_col in c("Age", "SibSp", "Parch", "Fare")) {
  titanic[[numeric_col]] <- as.numeric(titanic[[numeric_col]])
}

#### Dummyize Data for XGB
factor_vars <- names(titanic)[sapply(titanic, is.factor)]
for (factor_var in factor_vars) {
  dummy_vars <-  data.frame(model.matrix(as.formula(paste0("~titanic$", factor_var))))
  names(dummy_vars) <- paste(factor_var, seq_along(dummy_vars), sep = "_")
  titanic <<- cbind(dplyr::select_(titanic, paste0("-", factor_var)), dummy_vars)
}


##### Separate Into Train, Validation, and Test for XGB
TEST_PCT <- 0.1
is_train_data <- (runif(NROW(titanic)) > TEST_PCT)
titanic_train <- titanic[is_train_data,]
titanic_test <- titanic[!is_train_data,]
dep_var_train <- (as.numeric(dep_var[is_train_data]) - 1)
dep_var_test <- (as.numeric(dep_var[!is_train_data]) - 1)

VALIDATION_PCT <- 0.1
is_validation_data <- (runif(NROW(titanic_train)) > VALIDATION_PCT)
titanic_validation <- titanic_train[is_validation_data,]
titanic_train <- titanic_train[!is_validation_data,]
dep_var_validation <- dep_var_train[is_validation_data]
dep_var_train <- dep_var_train[!is_validation_data]


#### Turn data into matrix for XGB
titanic_train <- xgboost::xgb.DMatrix(data = as.matrix(titanic_train), label = dep_var_train)
titanic_validation <- xgboost::xgb.DMatrix(data = as.matrix(titanic_validation), label = dep_var_validation)
titanic_test <- xgboost::xgb.DMatrix(data = as.matrix(titanic_test), label = dep_var_test)

watchlist <- list(train = titanic_train, test = titanic_validation)
model <- xgboost::xgboost(data = titanic_train,
  nrounds = 400, learning_rate = 0.05, max_depth = 2, eta = 1, objective = "binary:logistic",
  nthread = 2,
  objective = "binary:logistic", watchlist = watchlist)


## Get Test AUC
preds <- xgboost::predict(model, titanic_test)
message("AUC: ", pROC::auc(preds, dep_var_test))
timer_end <- Sys.time()
message("Time: ", timer_end - timer_start, "s")
# AUC: 0.5
# Time: 1.3565149307251s
# TODO: WTF?

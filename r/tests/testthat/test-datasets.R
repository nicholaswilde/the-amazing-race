test_that("all 7 datasets exist and have expected structure", {
  expect_true(exists("seasons"))
  expect_true(exists("episodes"))
  expect_true(exists("contestants"))
  expect_true(exists("teams"))
  expect_true(exists("legs"))
  expect_true(exists("leg_results"))
  expect_true(exists("tasks"))

  tables <- list(
    seasons = seasons,
    episodes = episodes,
    contestants = contestants,
    teams = teams,
    legs = legs,
    leg_results = leg_results,
    tasks = tasks
  )

  for (name in names(tables)) {
    df <- tables[[name]]
    expect_s3_class(df, "data.frame")
    expect_gt(nrow(df), 0)
    expect_gt(ncol(df), 0)
    expect_true("season" %in% names(df))
    expect_true("version" %in% names(df))
  }
})

test_that("seasons dataset has all 36 seasons", {
  expect_gte(nrow(seasons), 36)
  expect_true(is.integer(seasons$season))
})

test_that("leg_results has boolean flag columns", {
  expect_true(is.logical(leg_results$is_non_elimination))
  expect_true(is.logical(leg_results$fast_forward))
})

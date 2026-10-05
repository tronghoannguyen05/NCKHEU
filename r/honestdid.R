# Rambachan and Roth (2023) sensitivity analysis for violations of parallel trends.
#
# Input: output/honestdid/*.json written by the Python pipeline. Each file holds the
# Callaway-Sant'Anna event-study estimates with a universal base period (reference e = -1
# excluded), their bootstrap covariance, and l_vec (average of the post-period effects
# listed in config/settings.yaml, honestdid.post_average_e).
#
# Output: output/honestdid/<name>_relative_magnitudes.csv, <name>_smoothness.csv and a plot.
#
# Requirements: install.packages(c("jsonlite", "remotes")); remotes::install_github("asheshrambachan/HonestDiD")
# This script has not been run in the development environment (no R there). Run it once on
# the synthetic output (`python -m idsp.pipeline --synthetic`) before the real analysis.

suppressPackageStartupMessages({
  library(jsonlite)
  library(HonestDiD)
})

mbar <- c(0, 0.5, 1, 1.5, 2)   # keep equal to config/settings.yaml honestdid.mbar
files <- list.files("output/honestdid", pattern = "\\.json$", full.names = TRUE)
if (length(files) == 0) stop("No input files. Run the Python pipeline first.")

for (f in files) {
  x <- fromJSON(f)
  name <- sub("\\.json$", "", basename(f))
  betahat <- as.numeric(x$betahat)
  sigma <- as.matrix(x$sigma)
  npre <- x$numPrePeriods
  npost <- x$numPostPeriods
  l_vec <- matrix(as.numeric(x$l_vec), ncol = 1)
  if (npre < 1) { message(name, ": no pre-periods, skipped"); next }

  original <- constructOriginalCS(betahat = betahat, sigma = sigma, numPrePeriods = npre,
                                  numPostPeriods = npost, l_vec = l_vec)
  rm_res <- createSensitivityResults_relativeMagnitudes(
    betahat = betahat, sigma = sigma, numPrePeriods = npre, numPostPeriods = npost,
    Mbarvec = mbar, l_vec = l_vec)
  write.csv(rm_res, file.path("output/honestdid", paste0(name, "_relative_magnitudes.csv")), row.names = FALSE)

  # Smoothness restriction: M in multiples of the standard error of the first post-period estimate.
  se1 <- sqrt(sigma[npre + 1, npre + 1])
  sm_res <- createSensitivityResults(betahat = betahat, sigma = sigma, numPrePeriods = npre,
                                     numPostPeriods = npost, method = "FLCI",
                                     Mvec = se1 * c(0, 0.25, 0.5, 1), l_vec = l_vec)
  write.csv(sm_res, file.path("output/honestdid", paste0(name, "_smoothness.csv")), row.names = FALSE)

  p <- createSensitivityPlot_relativeMagnitudes(rm_res, original)
  ggplot2::ggsave(file.path("output/figures", paste0(name, "_honestdid_rm.png")), p, width = 6, height = 4, dpi = 200)

  # Breakdown value: largest Mbar for which the robust interval excludes zero.
  ok <- rm_res$lb > 0 | rm_res$ub < 0
  bd <- if (any(ok)) max(rm_res$Mbar[ok]) else NA
  message(sprintf("%s [%s]: breakdown Mbar = %s", name, x$data, bd))
}

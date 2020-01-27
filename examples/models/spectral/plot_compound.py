r"""
.. _compound-spectral-model:

Compound Spectral Model
=======================

This model is formed by the arithmetic combination of any two other spectral models.
"""

# %%
# Example plot
# ------------
# Here is an example plot of the model:

from astropy import units as u
from gammapy.modeling.models import (
    Models,
    SkyModel,
    PowerLawSpectralModel,
    LogParabolaSpectralModel,
    CompoundSpectralModel
)
import operator

energy_range = [0.1, 100] * u.TeV
pwl = PowerLawSpectralModel(index=2.0, amplitude="1e-12 cm-2 s-1 TeV-1", reference="1 TeV")
lp = LogParabolaSpectralModel(amplitude="1e-12 cm-2 s-1 TeV-1", reference="10 TeV", alpha=2.0, beta=1.0)
compound = CompoundSpectralModel(pwl, lp, operator.add)
compound.plot(energy_range);

# %%
# YAML representation
# -------------------
# Here is an example YAML file using the model:

model = SkyModel(spectral_model=compound)
models = Models([model])

print(models.to_yaml())

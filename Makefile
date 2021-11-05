run:
	FitR aux/fit_files/2021-10-10-15-49-39_fitfiletools.fit

test: update-profile
	FitR aux/fit_files/2021-10-10-15-49-39_fitfiletools.fit

dev-install:
	pip install -e .

update-profile:
	tools/parse_profile.py aux/FitSDKRelease_21.67.00/Profile.xlsx > src/fitr/profile.py

black-profile:
	black src/fitr/profile.py

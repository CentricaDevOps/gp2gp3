# gp2gp3 project

This project will automatically migrate EBS volumes from gp2 to gp3.

See [documentation](doc/README.md) for full documentation.

The intention is to minimise the possible impact of such a migration by processing each volume individually per region per
account.  The code will wait for the gp3 optimisation to conclude before migrating the next volume in a region in an account.

I suspect that under the hood, AWS use the existing snapshot mechanism to achieve this.  The only volumes that cannot be
automatically migrated by this code are the ones that are attached to some older families of instances.  Hopefully, they'll be
few and far between.

The code runs every 15 minutes in every account and region of that account.

## Count GP2 Volumes
The Lambdas can be run in read only mode, whereby the gp3 transition for discovered gp2 volumes is disabled.

set the environment variable `TRANSITIONVOLUMES` to `true` for the volume transition to take place.

## Install

This project uses [AWS Chalice](https://chalice.readthedocs.io/en/stable/) for easy serveless deployment and [poetry](https://python-poetry.org/) for easy virtual environment management.  Install poetry with

```
python3 -m pip install poetry --user
```


As this contains some code from wavefront that requires compiling for the version of python that is going to be used ensure that
you install python 3.8 as that is the lambda runtime that is currently available.

```
poetry env use 3.8
make install
```
That will install all necessary modules into the virtual environment created by poetry and create a vendor directory for the base
lambda layer.

Make the AWS Chalice config directory
```
mkdir .chalice
```

Adjust the [Sample AWS Chalice Configuration](sample-config.json) for your AWS Organisation.

### Organisation Account Configuration

You will need to replace `AWS-ACCOUNT-NUMBER`, `AWS-REGION`, `YOUR-AWS-ORGANISATION-NAME`, `YOUR-AWS-ORGANISATION-ID`, `YOUR-WF-TENENT`

```
sed -e 's/AWS-ACCOUNT-NUMBER/012345678901/' \
-e 's/AWS-REGION/eu-west-1/' \
-e 's/YOUR-AWS-ORGANISATION-ID/o-123456/' \
-e 's/YOUR-AWS-ORGANISATION-NAME/The Wibble Factory/' \
-e 's/YOUR-WF-TENENT/wibble-factory/' \
sample-config.json >.chalice/config.json
```

### Environment Variables

Set the following environment variables as required in the config file:

* `TRANSITIONVOLUMES` - set to 'false' to just count gp2 disks
* `IGNOREDISKS` - size in GB, any disk greater than this size will be skipped.
* `OLDESTFIRST` - set to "true" by default, will transition the disks in order of age.
* `WAVEFRONT_URL` - the url for direct ingestion by Wavefront.
* `WFSSMPATH` - the parameter store path to the Wavefront credential.
* `SNOWSRV` - the parameter store sub-path to the Service-Now credentials.

Save this file as `.chalice/config.json`


You will need an AWS profile for the organisation account. Adjust the [Makefile](Makefile) to your needs.  The Director and
Worker Lambdas require a pre-defined role to run, create these roles with:

```
aws --profile your-profile --region your-region \
cloudformation create-stack \
--capabilities CAPABILITY_NAMED_IAM \
--stack-name sreGP23DirectorRoleCF \
--template-body file://cloudformation/gp23-director-role.yaml

aws --profile your-profile --region your-region \
cloudformation create-stack \
--capabilities CAPABILITY_NAMED_IAM \
--stack-name sreGP23WorkerRoleCF \
--template-body file://cloudformation/gp23-worker-role.yaml
```

To deploy the lambdas
```
make deploy
```

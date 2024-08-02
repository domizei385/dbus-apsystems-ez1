#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SERVICE_NAME=$(basename $SCRIPT_DIR)

# set permissions for script files
chmod a+x $SCRIPT_DIR/restart.sh
chmod 744 $SCRIPT_DIR/restart.sh

chmod a+x $SCRIPT_DIR/uninstall.sh
chmod 744 $SCRIPT_DIR/uninstall.sh

chmod a+x $SCRIPT_DIR/service/run
chmod 755 $SCRIPT_DIR/service/run

wget -c -O aiohttp-3.9.3-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl https://files.pythonhosted.org/packages/45/96/a5c44383ff60bb3d0f0a74e55cbe15e90ab54de4a00c1510e2723d5984b0/aiohttp-3.9.3-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
unzip -n aiohttp-3.9.3-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl

wget -c -O attrs-23.2.0-py3-none-any.whl https://files.pythonhosted.org/packages/e0/44/827b2a91a5816512fcaf3cc4ebc465ccd5d598c45cefa6703fcf4a79018f/attrs-23.2.0-py3-none-any.whl
unzip -n attrs-23.2.0-py3-none-any.whl

wget -c -O aiohappyeyeballs-2.3.4-py3-none-any.whl https://files.pythonhosted.org/packages/93/fd/a19345071360a94345ebecaa268d6c6f56900687d91ef775fe2496a76100/aiohappyeyeballs-2.3.4-py3-none-any.whl
unzip -n aiohappyeyeballs-2.3.4-py3-none-any.whl

wget -c -O aiosignal-1.3.1-py3-none-any.whl https://files.pythonhosted.org/packages/76/ac/a7305707cb852b7e16ff80eaf5692309bde30e2b1100a1fcacdc8f731d97/aiosignal-1.3.1-py3-none-any.whl
unzip -n aiosignal-1.3.1-py3-none-any.whl

wget -c -O frozenlist-1.4.1-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl https://files.pythonhosted.org/packages/3b/75/30ff63c92b4c561803662bb7e75b5a6863a2af434e6ff05be8a514a41dd2/frozenlist-1.4.1-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
unzip -n frozenlist-1.4.1-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl

wget -c -O multidict-6.0.5-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl https://files.pythonhosted.org/packages/7d/b6/fd8dd4a1ce1d129a1870143133f449b769ae236e9435ed8d74a8d45acb8e/multidict-6.0.5-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
wget -c -O yarl-1.9.4-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl https://files.pythonhosted.org/packages/16/07/719c440f9009c0e7293181f5adb72ba102e4b64312069d03a2bf9b68e97f/yarl-1.9.4-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
wget -c -O async_timeout-4.0.3-py3-none-any.whl https://files.pythonhosted.org/packages/a7/fa/e01228c2938de91d47b307831c62ab9e4001e747789d0b05baf779a6488c/async_timeout-4.0.3-py3-none-any.whl
unzip -n async_timeout-4.0.3-py3-none-any.whl
unzip -n yarl-1.9.4-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl
unzip -n multidict-6.0.5-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl

# create sym-link to run script in deamon
ln -s $SCRIPT_DIR/service /service/$SERVICE_NAME

# add install-script to rc.local to be ready for firmware update
filename=/data/rc.local
if [ ! -f $filename ]
then
    touch $filename
    chmod 755 $filename
    echo "#!/bin/bash" >> $filename
    echo >> $filename
fi

grep -qxF "$SCRIPT_DIR/install.sh" $filename || echo "$SCRIPT_DIR/install.sh" >> $filename

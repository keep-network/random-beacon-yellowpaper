class Request(NamedTuple):
    seedCommitment:  Commitment[SeedValue]
    requesterPubkey: EcdsaPubkey
    stakeMultiplier: Float
    placedAt:        Blockheight
    openTimeout:     Blockheight
    previousOutput:  BlsSignature

def openCommitment(requestID, seed_i):
    request_i = Requests[requestID] # abort if no such request
    senderPubkey = getSenderPubkey()
    T_open = getCurrentBlockheight()

    # ignore commitment openings that arrive too late
    if T_open > request_i.openTimeout:
        abort()

    # ignore commitment openings by parties other than original requester
    if not request_i.requesterPubkey == senderPubkey:
        abort()

    # ignore invalid commitment openings
    if not request_i.seedCommitment == sha3(seed_i, senderPubkey):
        abort()

    Block_kPlus1 = getBlockByHeight(request_i.placedAt + 1)
    v_r = Block_kPlus1.blockhash

    Group_i = select(AllGroups, v_r)
    v_iMinus1 = request_i.previousOutput
    toSign = sha3(seed_i, v_r, v_iMinus1)

    outputWaiting = OpenOutput(
        startedAt    = T_open,
        signingGroup = Group_i,
        valueToSign  = toSign
    )

    OutputInProgress[requestID] = outputWaiting


def receiveOutput(requestID, outputSignature):
    outputWaiting = OutputInProgress[requestID] # abort if not found
    request_i = Requests[requestID]

    pubkey_Group_i = outputWaiting.signingGroup.groupPubkey
    valueToSign = outputWaiting.valueToSign

    submitter = getSenderPubkey()

    signatureValid = blsVerify(
        outputSignature,
        valueToSign,
        pubkey_Group_i
    )

    if signatureValid:
        T_output = getCurrentBlockHeight() - outputWaiting.startedAt

        rewardGroup(
            submitter,
            group_i,
            T_output,
            request_i.stakeMultiplier
        )

    else:
        punish(
            submitter,
            INVALID_SIGNATURE_PENALTY * request_i.stakeMultiplier
        )


// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/governance/Governor.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";
import "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol";

contract EchoGovernor is
    Governor,
    GovernorSettings,
    GovernorCountingSimple,
    GovernorVotes,
    GovernorVotesQuorumFraction
{
    event GlyphProposal(string description);

    constructor(IVotes _token)
        Governor("EchoDAO")
        GovernorSettings(1, 45818, 0)
        GovernorVotes(_token)
        GovernorVotesQuorumFraction(4)
    {}

    function propose(
        address[] memory targets,
        uint256[] memory values,
        bytes[] memory calldatas,
        string memory description
    )
        public
        override
        returns (uint256)
    {
        emit GlyphProposal(description);
        return super.propose(targets, values, calldatas, description);
    }
}

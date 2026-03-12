using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[Serializable]
public class StartSessionRequest
{
    public string entrepreneur_name;
    public string mode;
    public BusinessIdeaData business_idea;
    public List<JudgeDefinition> judges;
}

[Serializable]
public class BusinessIdeaData
{
    public string name;
    public string description;
    public string target_market;
    public string revenue_model;
    public string current_traction;
    public string investment_needed;
    public string use_of_funds;
}

[Serializable]
public class JudgeDefinition
{
    public string id;
    public string name;
    public string role;
    public string goal;
    public string backstory;
}

[Serializable]
public class NextTurnRequest
{
    public string session_id;
    public string user_message;
}

[Serializable]
public class SessionTurnResponse
{
    public string session_id;
    public int turn;
    public string scene;
    public List<AgentMessage> messages;
    public UiHints ui_hints;
    public string conversation_status;
}

[Serializable]
public class AgentMessage
{
    public string message_id;
    public string agent_id;
    public string agent_name;
    public string agent_role;
    public string text;
    public string emotion;
    public string animation;
    public string ui_target;
    public string timestamp;
}

[Serializable]
public class UiHints
{
    public string layout;
    public bool show_typing_effect;
    public bool auto_advance;
}
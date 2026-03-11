using UnityEngine;

public class DemoBootstrap : MonoBehaviour
{
    [SerializeField] private SharkTankUIManager uiManager;

    private void Start()
    {
        // Start the demo pitch session automatically
        if (uiManager != null)
        {
            uiManager.StartPitch();
        }
        else
        {
            Debug.LogError("UIManager not assigned in DemoBootstrap.");
        }
    }
}
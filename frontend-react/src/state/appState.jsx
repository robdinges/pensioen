import { createContext, useContext, useMemo, useReducer } from "react";

const AppStateContext = createContext(null);

const initialState = {
  activeStep: "personen",
  currentHousehold: "Standaard huishouden",
  activeScenario: "Basisscenario",
  calculationStatus: "idle",
  lastCalculatedAt: null,
  autosaveStatus: "saved",
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_ACTIVE_STEP":
      return state.activeStep === action.payload ? state : { ...state, activeStep: action.payload };
    case "SET_CONTEXT": {
      const nextCurrentHousehold = action.payload.currentHousehold ?? state.currentHousehold;
      const nextActiveScenario = action.payload.activeScenario ?? state.activeScenario;
      if (
        nextCurrentHousehold === state.currentHousehold &&
        nextActiveScenario === state.activeScenario
      ) {
        return state;
      }
      return {
        ...state,
        currentHousehold: nextCurrentHousehold,
        activeScenario: nextActiveScenario,
      };
    }
    case "SET_CALC_STATUS":
      return state.calculationStatus === action.payload
        ? state
        : { ...state, calculationStatus: action.payload };
    case "MARK_STALE":
      return state.calculationStatus === "calculating" || state.calculationStatus === "stale"
        ? state
        : {
            ...state,
            calculationStatus: "stale",
          };
    case "MARK_FRESH":
      return {
        ...state,
        calculationStatus: "fresh",
        lastCalculatedAt: action.payload,
      };
    case "SET_AUTOSAVE_STATUS":
      return state.autosaveStatus === action.payload
        ? state
        : {
            ...state,
            autosaveStatus: action.payload,
          };
    default:
      return state;
  }
}

export function AppStateProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const actions = useMemo(
    () => ({
      setActiveStep: (step) => dispatch({ type: "SET_ACTIVE_STEP", payload: step }),
      setContext: (payload) => dispatch({ type: "SET_CONTEXT", payload }),
      setCalcStatus: (status) => dispatch({ type: "SET_CALC_STATUS", payload: status }),
      markStale: () => dispatch({ type: "MARK_STALE" }),
      markFresh: () => dispatch({ type: "MARK_FRESH", payload: new Date().toISOString() }),
      setAutosaveStatus: (status) => dispatch({ type: "SET_AUTOSAVE_STATUS", payload: status }),
    }),
    [],
  );

  const value = useMemo(
    () => ({ state, actions }),
    [state, actions],
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState() {
  const value = useContext(AppStateContext);
  if (!value) {
    throw new Error("useAppState must be used inside AppStateProvider");
  }
  return value;
}
